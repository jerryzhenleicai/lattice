package org.lattice.examples;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class C {
	static Logger logger =  LoggerFactory.getLogger(C.class);
	public String toString() {
		logger.info("C.toString()");
		return "I am a C object";
	}

}