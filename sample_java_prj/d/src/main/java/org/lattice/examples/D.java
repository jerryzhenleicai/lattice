package org.lattice.examples;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class D {
	static Logger logger =  LoggerFactory.getLogger(D.class);
	public String toString() {
		logger.info("D.toString()");
		return "I am a D object";
	}

}