digraph workflow1 {
	A 		-> B;
	B 		-> AND1;
	AND1 [AND] 	-> E, OR1;
	OR1 [OR] 	-> [0.15] C, [0.85] D;
	E [0.5] 	-> AND2;
	C 		-> OR2;
	D 		-> OR2;
	OR2 [OR] 	-> AND2;
	AND2 [AND] 	-> F;
}