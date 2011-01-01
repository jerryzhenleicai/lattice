package org.lattice.examples;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class F {
	static Logger logger =  LoggerFactory.getLogger(F.class);
	private C c = new C();
	private D d = new D();

	public String toString() {
		logger.info("F.toString()");
		return "F object, Members: [ " + c + "," + d + "]"  ;
	}

}