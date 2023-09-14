package com.openfaas.function;

import java.util.Map;
import java.util.Arrays;
import java.util.HashMap;
import com.openfaas.model.IRequest;
import com.openfaas.model.IResponse;
import com.openfaas.model.Request;
import com.openfaas.model.Response;

import java.util.Random;

public class Handler implements com.openfaas.model.IHandler {
	
    private static int dimension; /* Preset for the dimensionality of matrices */
    private static double mutability; /* Workload Variance */
    private static int seed = 42;
    static Random random = new Random(seed);

    private static final int dimMin = 10; /* Preset for the minimum of matrix dimension */
    private static final int dimMax = 50; /* Preset for the maximum of matrix dimension */
    private static final double scalingFactor = 2; /* Preset for scaling the mutability for matrix dimension */

    private static int[][] multiplier = new int[dimension][dimension];
	private static int[][] multiplicand = new int[dimension][dimension];

    public static double generateWorkload(double mutability, double min, double max, double scalingFactor) {
        double nextGaussian = random.nextGaussian() * (Math.sqrt(mutability) * scalingFactor) + (min + max) / 2;
        if (nextGaussian < min) return min;
        if (nextGaussian > max) return max;
        return nextGaussian;
    }

	private static int[][] matrixMultiplication(int[][] multiplier, int[][] multiplicand) {
        int[][] result = new int[dimension][dimension];
        for (int row = 0; row < dimension; row++) {
            for (int column = 0; column < dimension; column++) {
                result[row][column] = dotProduct(getRowVector(multiplier, row), getColumnVector(multiplicand, column));
            }
        }
        return result;
	}

    private static int[] getRowVector(int[][] matrix, int rowIndex) {
        int[] rowVector = new int[dimension];
        for (int i = 0; i < dimension; i++) {
            rowVector[i] = matrix[rowIndex][i];
        }
        return rowVector;
    }

    private static int[] getColumnVector(int[][] matrix, int columnIndex) {
        int[] columnVector = new int[dimension];
        for (int i = 0; i < dimension; i++) {
            columnVector[i] = matrix[i][columnIndex];
        }
        return columnVector;
    }

    private static int dotProduct(int[] rowVector, int[] columnVector) {
        int result = 0;
        for(int i = 0; i < dimension; i++) {
            result += (rowVector[i] * columnVector[i]);
        }
        return result;
    }

    private static int[][] generateMatrix() {
        int cellMin = -100;
        int cellMax = 100;
        int[][] generatedMatrix = new int[dimension][dimension];
        for (int row = 0; row < dimension; row++) {
          for(int column = 0; column < dimension; column++) {
             generatedMatrix[row][column] = random.nextInt(cellMax - cellMin + 1) + cellMin;
          }
        }
        return generatedMatrix;
    }


	private static long benchmark() {
        dimension = (int) Math.round(generateWorkload(mutability, dimMin, dimMax, scalingFactor));
        multiplier = generateMatrix();
        multiplicand = generateMatrix();
        long startTime = System.nanoTime();
        int[][] matrix = matrixMultiplication(multiplier, multiplicand);
        long finishTime = System.nanoTime();
        return (finishTime - startTime) / 1000;
    }
    
    public IResponse Handle(IRequest req) {
        Response res = new Response();
        Map<String, String> query = req.getQuery();
        mutability = Double.parseDouble(query.get("mutability"));
        long serverTime = benchmark();
        res.setBody(String.format("MatrixMultiplication took %d ms", serverTime));
        return res;
    }

    @Override
    public IResponse Warm() {
		Response res = new Response();
        return res;
    }

}