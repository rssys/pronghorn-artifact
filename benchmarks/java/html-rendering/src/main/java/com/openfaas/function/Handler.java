package com.openfaas.function;

import java.io.IOException;
import java.io.StringWriter;
import java.util.Arrays;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;

import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

import com.github.mustachejava.DefaultMustacheFactory;
import com.github.mustachejava.Mustache;
import com.github.mustachejava.MustacheFactory;

import java.util.Random;

public class Handler implements com.openfaas.model.IHandler {

  static ArrayList<Item> itemList;
	static double mutability; /* Workload Variance */
	static int seed = 42;
	static Random random = new Random(seed);

	static int numItems;

	static final int itemsMin = 100; /* Preset for the minimum of data length */
	static final int itemsMax = 500; /* Preset for the maximum of data length */
	static final double scalingFactor = (itemsMax / 20); /* Preset for scaling the mutability for length of data to be displayed */

  List<Item> items() {
		return itemList;
	}
	
	static class Item {
		Item(String name, String price, List<Feature> features) {
			this.name = name;
			this.price = price;
			this.features = features;
		}
		String name, price;
		List<Feature> features;
	}

	static class Feature {
		Feature(String description) {
			this.description = description;
		}
		String description;
  }

	static class HTMLRendering {

		HTMLRendering(int numItems) {
			itemList = new ArrayList<>();
			for (int i = 0; i < numItems; i++) {
				itemList.add(new Item("Item " + i, "$" + i + "." + i, Arrays.asList(new Feature("New! #" + i), new Feature("Awesome! #" + i))));
			}
		}

	}
  
  public static double generateWorkload(double mutability, double min, double max, double scalingFactor) {
			double nextGaussian = random.nextGaussian() * (Math.sqrt(mutability) * scalingFactor) + (min + max) / 2;
			if (nextGaussian < min) return min;
			if (nextGaussian > max) return max;
			return nextGaussian;
  }

  private static long benchmark() throws IOException {
		StringWriter writer = new StringWriter();
		numItems = (int) generateWorkload(mutability, itemsMin, itemsMax, scalingFactor);
		HTMLRendering renderer = new HTMLRendering(numItems);
		long startTime = System.nanoTime();
		MustacheFactory mf = new DefaultMustacheFactory();
		Mustache mustache = mf.compile("resource.mustache");
		mustache.execute(writer, renderer).flush();
		long finishTime = System.nanoTime();
		writer.getBuffer().setLength(0);
		return (finishTime - startTime) / 1000;
	}

    
	public IResponse Handle(IRequest req) {
      Response res = new Response();
      Map<String, String> query = req.getQuery();
      mutability = Float.parseFloat(query.get("mutability"));
      long serverTime;
      try {
        serverTime = benchmark();
      } catch (java.io.IOException e) {
        res.setBody(e.toString());
        return res;
      }
      res.setBody(String.format("HTMLRendering took %d ms", serverTime));
      return res;
  }

    @Override
    public IResponse Warm() {
      Response res = new Response();
      return res;
    }

}