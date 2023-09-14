package com.openfaas.function;

import java.util.Map;
import java.util.HashMap;
import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

import java.util.Random;
import java.io.IOException;
import java.nio.file.Path;
import java.io.File;
import java.nio.charset.Charset; 
import com.google.common.io.Files;
import com.google.gson.Gson;

public class Handler implements com.openfaas.model.IHandler {
	
	private static double mutability; /* User specified value for workload scalability constant */
    private static int seed = 42;
	private static Random random = new Random(seed);

	private static final int recordsMin = 200; /* Preset for the minimum of words read */
	private static final int recordsMax = 1000; /* Preset for the maximum of words read */
	private static final double scalingFactor = (recordsMax / 20); /* Preset for scaling the mutability for length of data to be hashed */
	
	private class JSONData {
		int idx;
		String str;
	}

	public static double generateWorkload(double mutability, double min, double max, double scalingFactor) {
        double nextGaussian = random.nextGaussian() * (Math.sqrt(mutability) * scalingFactor) + (min + max) / 2;
        if (nextGaussian < min) return min;
        if (nextGaussian > max) return max;
        return nextGaussian;
    }

	private static long benchmark() throws IOException {
		Gson gson = new Gson();
        File input = new File("resource.json");
		String data = Files.toString(input, Charset.forName("UTF-8"));
		String[] records = data.substring(1, data.length() - 2).split(",\n");
        int recordsCount = (int) generateWorkload(mutability, recordsMin, recordsMax, scalingFactor);
        long startTime = System.nanoTime();
        JSONData jData = null;
        for (int j = 0; j < recordsCount; j++) {
            jData = gson.fromJson(records[j], JSONData.class);	
        }
        long finishTime = System.nanoTime();
        return (finishTime - startTime) / 1000;
    }
    
    public IResponse Handle(IRequest req) {
        Response res = new Response();
        Map<String, String> query = req.getQuery();
        mutability = Double.parseDouble(query.get("mutability"));
		long serverTime;
        try {
            serverTime = benchmark();
        } catch (IOException e) {
            res.setBody(e.toString());
            return res;
        }
        res.setBody(String.format("JSONParsing took %d ms", serverTime));
        return res;
    }

    @Override
    public IResponse Warm() {
		Response res = new Response();
        return res;
    }

}