TEXBIN ?= /Library/TeX/texbin
LATEXMK ?= $(TEXBIN)/latexmk
XELATEX ?= $(TEXBIN)/xelatex
BIBTEX ?= $(TEXBIN)/bibtex

.PHONY: all clean

all: final_report_en.pdf final_report_zh.pdf

final_report_en.pdf: final_report_en.tex references.bib
	$(LATEXMK) -xelatex -interaction=nonstopmode -halt-on-error final_report_en.tex

final_report_zh.pdf: final_report_zh.tex references.bib
	$(LATEXMK) -xelatex -interaction=nonstopmode -halt-on-error final_report_zh.tex

clean:
	$(LATEXMK) -C final_report_en.tex final_report_zh.tex
