// Copyright (c) OpenFaaS Author(s) 2018. All rights reserved.
// Licensed under the MIT license. See LICENSE file in the project root for full license
// information.

package com.openfaas.model;

import java.util.HashMap;

public class SampleHandler implements IHandler {
    @Override
    public IResponse Handle(IRequest request) {
        return new Response();
    }

    @Override
    public IResponse Warm() {
        return this.Handle(new Request("", new HashMap<String, String>()));
    }
}
