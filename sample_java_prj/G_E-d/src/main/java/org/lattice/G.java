package org.lattice;
import org.lattice.examples.D;
import org.lattice.examples.E;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;


public class G {
	static Logger logger =  LoggerFactory.getLogger(G.class);
	private E e = new E();
	private D d = new D();
	
	public G() {
		
	}
	
	public G(String val) {
		e = new E(val);
	}

	public String toString() {
		logger.info("G.toString()");
		return "G object, Members: [ " + e + "," + d + "]"  ;
	}
	
	public static void main(String args[]) {
		System.out.println("Args : ");
		for (String arg  : args) {
			System.out.println("\t" + arg);
		}
	}

}