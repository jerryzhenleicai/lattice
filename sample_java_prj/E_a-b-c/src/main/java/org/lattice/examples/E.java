package org.lattice.examples;

import org.apache.commons.codec.binary.Base64;
import org.apache.commons.lang.RandomStringUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class E {
	static Logger logger = LoggerFactory.getLogger(E.class);
	private A a = new A();
	private B b = new B();
	private C c = new C();
	private String str = RandomStringUtils.random(6, "abcdefghijklmnopqrstuvwxyz");

	public E() {
		
	}
	
	public E(String val) {
		str = val;
	}
	
	public String toString() {
		logger.info("E.toString()");
		try {
			String coded = Base64.encodeBase64String(str.getBytes());
			return "E object, value " + str + ", BASE64 " + coded + ". Other members: [ " + a + "," + b
					+ "," + c + "]";
		} catch (Exception e) {
			throw new RuntimeException(e);
		}
	}

	public String getStr() {
		return str;
	}

	public void setStr(String str) {
		this.str = str;
	}
}