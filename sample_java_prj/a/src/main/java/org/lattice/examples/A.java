package org.lattice.examples;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class A {
	static Logger logger =  LoggerFactory.getLogger(A.class);
	public String toString() {
		logger.info("A.toString()");
		return "I am a A object";
	}

}