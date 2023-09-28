package com.openfaas.function;

import java.util.HashMap;
import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

public class Handler implements com.openfaas.model.IHandler {

    public IResponse Handle(IRequest req) {
        Response res = new Response();
        return res;
    }

    @Override
    public IResponse Warm() {
        // TODO Auto-generated method stub
        return this.Handle(new Request("", new HashMap<String, String>()));
    }

}
