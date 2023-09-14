package com.openfaas.function;

import java.util.Map;
import java.util.HashMap;
import java.util.Random;
import java.io.File;
import java.nio.file.Path;
import java.nio.charset.Charset; 
import java.util.Arrays;
import java.util.List;
import com.google.common.io.Files;
import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

public class Handler implements com.openfaas.model.IHandler {
	
	private static double mutability; /* User specified value for workload scalability constant */
	private static int seed = 42;
	static Random random = new Random(seed);

	private static final int wordMin = 5000; /* Preset for the minimum of words read */
	private static final int wordMax = 15000; /* Preset for the maximum of words read */
	private static final double scalingFactor = (wordMax / 20); /* Preset for scaling the mutability for length of data to be hashed */

	/**
	 * From https://www.java67.com/2016/09/3-ways-to-count-words-in-java-string.html
	 * @param  word
	 * @return
	 */

	private static int wordCount(String word) {
		if (word == null || word.isEmpty()) {
			return 0;
	  }

	  int wordCount = 0;

	  boolean isWord = false;
	  int endOfLine = word.length() - 1;
	  char[] characters = word.toCharArray();

	  for (int i = 0; i < characters.length; i++) {
	    // if the char is a letter, word = true.
	    if (Character.isLetter(characters[i]) && i != endOfLine) {
	      isWord = true;

	        // if char isn't a letter and there have been letters before,
	        // counter goes up.
	    } else if (!Character.isLetter(characters[i]) && isWord) {
	      wordCount++;
	      isWord = false;

	      // last word of String; if it doesn't end with a non letter, it
	      // wouldn't count without this.
	    } else if (Character.isLetter(characters[i]) && i == endOfLine) {
	      wordCount++;
	    }
	  }

		return wordCount;
	}

	public static double generateWorkload(double mutability, double min, double max, double scalingFactor) {
        double nextGaussian = random.nextGaussian() * (Math.sqrt(mutability) * scalingFactor) + (min + max) / 2;
        if (nextGaussian < min) return min;
        if (nextGaussian > max) return max;
        return nextGaussian;
    }

	private static long benchmark() throws java.io.IOException {
				File input = new File("resource.txt");
				List<String> data = Files.readLines(input, Charset.forName("UTF-8"));
        int linesCount = (int) generateWorkload(mutability, wordMin, wordMax, scalingFactor);
        String lineToRead = String.join("\n", data.subList(0, Math.min(linesCount, data.size())));
        long startTime = System.nanoTime();
        int count = wordCount(lineToRead);
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
				} catch (java.io.IOException e) {
					res.setBody(e.toString());
					return res;
				}
        res.setBody(String.format("WordCount took %d ms", serverTime));
        return res;
    }

    @Override
    public IResponse Warm() {
		    Response res = new Response();
        return res;
    }

}