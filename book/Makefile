SRC := text.md
PDF := book.pdf
PREAMBLE := preamble.tex
AFTER_TITLE := after-title.tex
TITLE := Kubernetes, GitOps, and All That
SUBTITLE := New Tricks for Old Dogs
AUTHOR := Will Ware
DATE := \today

GEOMETRY := paperwidth=8.5in,paperheight=11in,inner=1in,outer=0.5in,top=0.5in,bottom=0.5in,twoside

.PHONY: all clean

all: $(PDF)

$(PDF): $(SRC) $(PREAMBLE) $(AFTER_TITLE) glossary.tex
	pandoc $(SRC) \
		-o book.tex \
		--pdf-engine=xelatex \
		--from=markdown \
		--top-level-division=part \
		--number-sections \
		--include-in-header=$(PREAMBLE) \
		--include-before-body=$(AFTER_TITLE) \
		--variable=documentclass:book \
		--variable=classoption:openright \
		--variable=classoption:twoside \
		--variable=geometry:$(GEOMETRY) \
		--variable=title:"$(TITLE)" \
		--variable=subtitle:"$(SUBTITLE)" \
		--variable=author:"$(AUTHOR)" \
		--variable=date:"$(DATE)" \
		--variable=secnumdepth:0 \
		--toc
	xelatex book.tex
	makeglossaries book
	makeindex book
	xelatex book.tex
	xelatex book.tex
	@if [ "book.pdf" != "$(PDF)" ]; then mv book.pdf $(PDF); fi
	rm -f book.tex book.aux book.log book.out book.toc book.glo book.gls book.glg book.ist book.idx book.ilg book.ind

clean:
	rm -f $(PDF)
