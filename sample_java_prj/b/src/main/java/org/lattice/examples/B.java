package org.lattice.examples;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class B {
	static Logger logger =  LoggerFactory.getLogger(B.class);
	public String toString() {
		logger.info("B.toString()");
		return "I am a B object";
	}

}