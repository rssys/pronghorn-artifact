package com.openfaas.function;

import java.util.Map;
import java.util.HashMap;
import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

import java.util.Random;

public class Handler implements com.openfaas.model.IHandler {
	
		private static byte[] data;
		private static double mutability; /* Workload Variance */
		private static int seed = 42;
		static Random random = new Random(seed);

		private static final int lenMin = 50;
		private static final int lenMax = 500;
		private static final double scalingFactor = 75;

		public static double generateWorkload(double mutability, double min, double max, double scalingFactor) {
			double nextGaussian = random.nextGaussian() * (Math.sqrt(mutability) * scalingFactor) + (min + max) / 2;
			if (nextGaussian < min) return min;
			if (nextGaussian > max) return max;
			return nextGaussian;
    }

		private static int simpleHash(byte[] bytes) {
			int hash = 7;
			for (int i = 0; i < bytes.length; i++) {
				hash = hash*31 + bytes[i];
				hash = hash*31 + bytes[i];
				hash = hash*31 + bytes[i];
				hash = hash*31 + bytes[i];
			}
			return hash;
		}

		private static long benchmark() {
			data = new byte[1024 * (int) generateWorkload(mutability, lenMin, lenMax, scalingFactor)]; 
			random.nextBytes(data);
			long startTime = System.nanoTime();
			int hash = simpleHash(data);
			long finishTime = System.nanoTime();
			return (finishTime - startTime) / 1000;
		}
    
    public IResponse Handle(IRequest req) {
			Response res = new Response();
			Map<String, String> query = req.getQuery();
			mutability = Double.parseDouble(query.get("mutability"));
			long serverTime = benchmark();
			res.setBody(String.format("SimpleHash took %d ms", serverTime));
			return res;
    }

    @Override
    public IResponse Warm() {
				Response res = new Response();
        return res;
    }

}