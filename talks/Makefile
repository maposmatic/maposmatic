
all: lsm-2012.pdf

lsm-2012.pdf: lsm-2012.tex osm-database.pdf ocitysmap.pdf maposmatic.pdf hardware-setup.pdf
	pdflatex $^

%.pdf: %.svg
	inkscape -D -A $@ $<

%.pdf: %.eps
	epstopdf --outfile=$@ $^

%.eps: %.dia
	dia -e $@ -t eps $^

clean:
	$(RM) *.pdf *.pyg *.snm *.toc *.vrb *.aux *.nav *.out *.dia~ *.log
