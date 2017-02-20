def mm(in_l, field):
	st = ""
	for i in in_l:
		st += " OR \"" + field + "\" = " + str(i)
	return st
