// Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license
// information.

package com.openfaas.entrypoint;

import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpHandler;
import com.sun.net.httpserver.HttpServer;
import java.io.IOException;
import java.io.OutputStream;
import java.io.UnsupportedEncodingException;
import java.io.ByteArrayOutputStream;
import java.io.InputStream;
import java.net.InetSocketAddress;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.nio.file.StandardOpenOption;

import java.util.HashMap;
import java.util.Map;
import com.sun.net.httpserver.Headers;

import com.openfaas.model.*;

public class App {

    public static long APP_STARTUP_TIME;

    public static void main(String[] args) throws Exception {
        App.APP_STARTUP_TIME = System.nanoTime();
        int port = 8080;

        IHandler handler = new com.openfaas.function.Handler();

        HttpServer server = HttpServer.create(new InetSocketAddress(port), 0);
        InvokeHandler invokeHandler = new InvokeHandler(handler);
        WarmupHandler warmupHandler = new WarmupHandler(handler);

        server.createContext("/", invokeHandler);
        server.createContext("/warmup", warmupHandler);
        server.createContext("/_/health", warmupHandler);
        server.setExecutor(null); // creates a default executor
        server.start();
    }

    static class WarmupHandler implements HttpHandler {
        IHandler handler;

        private WarmupHandler(IHandler handler) {
            this.handler = handler;
        }

        @Override
        public void handle(HttpExchange t) throws IOException {
            IResponse res = this.handler.Warm();

            App.setResponse(t, res);
        }
    }

    static class InvokeHandler implements HttpHandler {
        IHandler handler;

        private InvokeHandler(IHandler handler) {
            this.handler = handler;
        }

        @Override
        public void handle(HttpExchange t) throws IOException {
            long requestArrivalTime = System.nanoTime();
            String requestBody = App.getRequestBody(t);

            Map<String, String> reqHeadersMap = App.getRequestHeaders(t);

            IRequest req = new Request(requestBody, reqHeadersMap, t.getRequestURI().getRawQuery(),
                    t.getRequestURI().getPath());

            long handleStartTime = System.nanoTime();
            IResponse res = this.handler.Handle(req);
            long latency = System.nanoTime() - handleStartTime;
            res.setHeader("X-Request-Arrival-Timestamp", String.valueOf(requestArrivalTime));
            res.setHeader("X-App-Startup-Timestamp", String.valueOf(App.APP_STARTUP_TIME));

            App.setResponse(t, res);

            try {
                String toWrite = res.getBody().split("took ")[1].split(" ms")[0] + "\n"; // String.format("%d\n",
                                                                                         // latency / 1000)
                Files.write(
                        Paths.get("./requestLog.txt"),
                        toWrite.getBytes(),
                        StandardOpenOption.APPEND);
            } catch (IOException e) {
                System.err.println("Could not write to file");
            }
        }
    }

    static public void setResponse(HttpExchange t, IResponse res)
            throws UnsupportedEncodingException, IOException {
        String response = res.getBody();
        byte[] bytesOut = response.getBytes("UTF-8");

        Headers responseHeaders = t.getResponseHeaders();
        String contentType = res.getContentType();
        if (contentType.length() > 0) {
            responseHeaders.set("Content-Type", contentType);
        }

        for (Map.Entry<String, String> entry : res.getHeaders().entrySet()) {
            responseHeaders.set(entry.getKey(), entry.getValue());
        }

        t.sendResponseHeaders(res.getStatusCode(), bytesOut.length);

        OutputStream os = t.getResponseBody();
        os.write(bytesOut);
        os.close();

        System.out.println("Request / " + Integer.toString(bytesOut.length) + " bytes written.");
    }

    static public Map<String, String> getRequestHeaders(HttpExchange t) {
        Headers reqHeaders = t.getRequestHeaders();
        Map<String, String> reqHeadersMap = new HashMap<String, String>();

        for (Map.Entry<String, java.util.List<String>> header : reqHeaders.entrySet()) {
            java.util.List<String> headerValues = header.getValue();
            if (headerValues.size() > 0) {
                reqHeadersMap.put(header.getKey(), headerValues.get(0));
            }
        }
        return reqHeadersMap;
    }

    static public String getRequestBody(HttpExchange t)
            throws IOException, UnsupportedEncodingException {
        String requestBody = "";
        String method = t.getRequestMethod();

        if (method.equalsIgnoreCase("POST")) {
            InputStream inputStream = t.getRequestBody();
            ByteArrayOutputStream result = new ByteArrayOutputStream();
            byte[] buffer = new byte[1024];
            int length;
            while ((length = inputStream.read(buffer)) != -1) {
                result.write(buffer, 0, length);
            }
            // StandardCharsets.UTF_8.name() > JDK 7
            requestBody = result.toString("UTF-8");
        }
        return requestBody;
    }
}
