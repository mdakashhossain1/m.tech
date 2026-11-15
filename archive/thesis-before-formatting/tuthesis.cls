
\NeedsTeXFormat{LaTeX2e}
\ProvidesClass{tuthesis}

\def\mystretch{1.5}		% 1.5 e spacing hack

%  Thesis looks much like report
\DeclareOption*{\PassOptionsToClass{\CurrentOption}{report}}
\ProcessOptions
\LoadClass{report}
\usepackage{setspace}
\usepackage{hyperref}
\usepackage{lscape}
\usepackage{minitoc}
\usepackage{fix2col}
\usepackage[pdftex]{graphicx}
\usepackage{multirow}
\usepackage{fancyhdr}
%\usepackage{longtable}
\usepackage{algcompatible}
\usepackage[lined,ruled,vlined]{algorithm2e}
% \RestyleAlgo{ruled}
\usepackage{ragged2e}
\usepackage{caption}
\usepackage{pdflscape}
\usepackage[noadjust]{cite}
\usepackage{rotating}
\usepackage{setspace}
\usepackage{etoolbox}
\usepackage{afterpage}
% appendix
\usepackage[toc,page]{appendix} 
\usepackage{listings}
\usepackage{xcolor}
\usepackage[a4paper,left=1.25in, right=1.25in, top=1.0in, bottom=1.0in]{geometry}
%----------------------------------pdf setup---------------------------------
\hypersetup{
    pdfstartview={FitH}
    pdfnewwindow=true,     % links in new window
    colorlinks=true,       % false: boxed links; true: colored links
    linkcolor=black,       % color of internal links (change box color with linkbordercolor)
    citecolor=blue,        % color of links to bibliography
}
%##################################### For .TpX file ################################################

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%% For Header %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\fancyhf{}
\lhead{\ifthenelse{\isodd{\value{page}}}{\bf \small {\nouppercase\rightmark}}{\bf \small{\nouppercase\leftmark}}}
\fancyfoot[C]{\thepage}
\pagestyle{fancy}
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

\usepackage{color}
\usepackage{ifpdf}
\ifpdf %if using pdfLaTeX in PDF mode
  \usepackage[pdftex]{graphicx}
  \DeclareGraphicsExtensions{.pdf,.png,.jpg,.jpeg,.mps}
  \usepackage{pgf}
  \usepackage{tikz}
\else %if using LaTeX or pdfLaTeX in DVI mode
  \usepackage{graphicx}
  \DeclareGraphicsExtensions{.eps,.bmp}
  \DeclareGraphicsRule{.emf}{bmp}{}{}% declare EMF filename extension
  \DeclareGraphicsRule{.png}{bmp}{}{}% declare PNG filename extension
  \usepackage{pgf}
  \usepackage{tikz}
  \usepackage{pstricks}
\fi
\usepackage{epic,bez123}
\usepackage{floatflt}% package for floatingfigure environment
\usepackage{wrapfig}% package for wrapfigure environment

%%%%%%%%%%%%%%to put a blan page%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
\newcommand\blankpage{%
    \null
    \thispagestyle{empty}%
    \addtocounter{page}{-1}%
    \newpage}

% If using the report style, use - instead of . in the figure number.
\@ifundefined{thechapter}{}{\def\thefigure{\thechapter-\arabic{figure}}}


%%%%%%%%%  End of Style parameters %%%%
