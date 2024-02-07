%%
%% This is file `ucph-revy.cls',
%% generated with the docstrip utility.
%%
%% The original source files were:
%%
%% ucph-revy.dtx  (with options: `class')
%% This is a generated file.
%% 
%% Copyright (C) 1995 Arne John Glenstrup
%%               2000 Uffe Friis Lichtenberg
%%               2023 Kristoffer Levin Hansen
%% 
%% This file may be distributed and/or modified under the
%% conditions of the LaTeX Project Public License, either
%% version 1.3 of this license or (at your option) any later
%% version. The latest version of this license is in:
%% 
%% http://www.latex-project.org/lppl.txt
%% 
%% and version 1.3 or later is part of all distributions of
%% LaTeX version 2005/12/01 or later.
\NeedsTeXFormat{LaTeX2e}[2005/12/01]
\ProvidesClass{ucph-revy}
    [2023/05/23 v1.0.0 Initial publish]
\RequirePackage{xstring}
\newif\if@thumbindex\@thumbindexfalse
\DeclareOption{thumbindex}{\@thumbindextrue}
\newcommand{\planfile}{aktoversigt.plan}
\DeclareOption*{
  \IfBeginWith{\CurrentOption}{planfile=}{
    \def\planfile#1=#2{#2}
    \edef\planfile{\expandafter\planfile\CurrentOption}
  }{
    \PassOptionsToClass{\CurrentOption}{article}
  }
}
\ProcessOptions\relax
\LoadClass[a4paper,11pt]{article}
\setlength{\topmargin}{0cm}
\setlength{\voffset}{-1cm}
\setlength{\textheight}{\paperheight}
\addtolength{\textheight}{-4cm}
\if@thumbindex
  \expandafter\@firstofone
\else
  \expandafter\@gobble
\fi{
  \RequirePackage[T1]{fontenc}
  \begingroup
    \count256=0
    \endlinechar=-1
    \newtoks\tabtoks
    \newread\tabtex
    \newread\planread
    \openin\planread=\planfile
    \def\expandFiHere#1\fi{\fi #1}
    \def\patheat#1/#2{%
      \ifx\relax#2\else
        \expandFiHere#1/\patheat#2%
      \fi
    }
    \edef\planpath{\expandafter\patheat\planfile/\relax}
    \def\titleeater#1#2\title#3{%
      \ifx\done#3%
        #1%
      \else
        \expandFiHere
        \titleeater{#3}%
      \fi
    }
    \loop\ifeof\planread
      \closein\planread
    \else
      \ifeof\tabtex
        \let\readline\empty
        \read\planread to \line
        \expandafter\ifx\expandafter\par\line\else
          \IfEndWith{\line}{.tex}{
            \advance\count256 by 1
            \set@curr@file{\line}
            \openin\tabtex={\planpath\@curr@file}
          }{%
            \edef\act{\noexpand\tabtoks={%
              \the\tabtoks
              \noexpand\undertab
              \number\count256
              \noexpand\text
              \line
              \noexpand\stop
            }}\act
          }
        \fi
      \else
        \read\tabtex to \subline
        \edef\readline{%
          \expandafter\titleeater
          \expandafter\readline\subline\title\done
        }
        \ifeof\tabtex
          \edef\act{\noexpand\tabtoks={%
              \the\tabtoks
              \noexpand\overtab
              \number\count256
              \noexpand\text
              \readline
              \noexpand\stop
            }}\act
        \fi
      \fi
    \repeat
    \closein\tabtex
    \edef\act{\noexpand\tabtoks={%
        \the\tabtoks
        \noexpand\undertab
        \number\count256
        \noexpand\text
        \noexpand\done
        \noexpand\stop
      }}\act
    \xdef\revy@tabs{\the\tabtoks}
  \endgroup
  \RequirePackage{tikz}
  \def\revy@thumbindex#1{%
    \begingroup
\def\expandFiHere##1\fi{\fi ##1}
      \newdimen\tabheight
      \tabheight=\paperheight
      \advance\tabheight by -1cm%
      \def\undertab##1\text##2\stop{
        \ifx\done##2%
          \divide\tabheight by \ifnum0=##1 1 \else ##1\fi%
        \fi
      }
      \def\overtab##1\text##2\stop{}%
      \revy@tabs
      \def\overtableft{-.75cm}
      \def\overtabright{.5cm}
      \def\undertabright{\overtabright}
      \def\undertableft{\overtableft - 1cm}
      \def\underangle{|-}
      \def\underpos{.25}
      \def\undersign{}
      \def\underlabeloffset{\undersign.5cm}
      \def\textanchorcorner{east}
      \def\textoffset{\undertableft - .5cm}
      \def\textside{right}
      \def\movetoleftside{
        \def\overtableft{-1.8cm}
        \def\overtabright{.2cm}
        \def\undertabright{\overtabright + 1cm}
        \def\undertableft{\overtableft}
        \def\underangle{-|}
        \def\undersign{-}
        \def\underpos{.75}
        \def\textanchorcorner{west}
        \def\textoffset{\undertabright + .5cm}
        \def\textside{left}
      }
\newif\ifwritetitles\writetitlesfalse
      \def\printovertab##1##2{
        \fill ( 0, -##1\tabheight )
        node[ text=white, anchor=east ]{\bfseries##1}
        +( \overtableft, -.5\tabheight + 1mm )
        rectangle +( \overtabright, .5\tabheight - 1mm )
        +( \textoffset, 0 )
        \ifwritetitles
          node[ anchor=\textanchorcorner ]{\small\bfseries##2}
        \fi
        ;
      }%
      \def\printundertab##1##2##3{%
        \path ( 0, -##1\tabheight ) +( \undertabright, -.5\tabheight - 1mm )
        coordinate (topright);
        \path ( 0, -##2\tabheight ) +( \undertableft, -.5\tabheight + 1mm )
        coordinate (bottomleft);
        \fill[ color=black!30 ] (topright) rectangle (bottomleft);
        \path (bottomleft)
        \underangle node[ xshift=\underlabeloffset,
        pos=\underpos,
        rotate=\undersign90
        ]{\Large##3}
        (topright);
      }%
      \def\overtab##1\text##2\stop{%
        \printovertab{##1}{##2}
      }
      \def\undertab##1\text##2\stop{
        \ifx\done##2\else
          \let\undertab\undertabspan
          \expandFiHere
          \undertab##1\text##2\stop
        \fi
      }
      \def\undertabspan##1\text##2\stop##3\undertab##4\text##5\stop{%
        \printundertab{##1}{##4}{##2}%
        ##3%
        \ifx\done##5\else
          \expandFiHere
          \undertab##4\text##5\stop
        \fi
      }%
      \def\filtername##1{
        \def\doWhenMatch{}
        \def\overtab####1\text####2\stop{
          \IfStrEq{##1}{####2}{
            \doWhenMatch
            \printovertab{####1}{####2}
          }{}
        }
        \def\undertabspan####1\text####2\stop####3\undertab####4\text####5\stop{
          \def\doWhenMatch{
            \printundertab{####1}{####4}{####2}
            \def\doWhenMatch{}
          }
          ####3
          \ifx\done####5\else
            \expandFiHere
            \undertab####4\text####5\stop
          \fi
        }
      }
      #1
      \begin{tikzpicture}
        \revy@tabs
        \path (0, 0) -- (0, -\paperheight + .5cm);
      \end{tikzpicture}
    \endgroup
  }
  \newcommand{\rectothumbtabfor}[1]{
    \revy@thumbindex{
      \filtername{#1}
    }
  }
  \newcommand{\rectothumbindexwithtitles}{
    \revy@thumbindex{
      \writetitlestrue
    }
  }
  \newcommand{\rectothumbindex}{
    \revy@thumbindex{}
  }
  \newcommand{\rectothumbtabwithtitlefor}[1]{
    \revy@thumbindex{
      \filtername{#1}
      \writetitlestrue
    }
  }
  \newcommand{\versothumbindex}{
    \revy@thumbindex{
      \movetoleftside
    }
  }
  \newcommand{\versothumbindexwithtitles}{
    \revy@thumbindex{
      \movetoleftside
      \writetitlestrue
    }
  }
  \newcommand{\versothumbtabfor}[1]{
    \revy@thumbindex{
      \movetoleftside
      \filtername{#1}
    }
  }
  \newcommand{\versothumbtabwithtitlefor}[1]{
    \revy@thumbindex{
      \movetoleftside
      \filtername{#1}
      \writetitlestrue
    }
  }
}
\def\version#1{\def\@version{#1}}
\def\@version{\@ifundefined{the@version}
{\typein[\versionsnr]{Indtast revytekstens versionsnummer: }%
\global\let\the@version=\versionsnr}{}\the@version}
\def\revyname#1{\def\@revyname{#1}}
\def\revyyear#1{\def\@revyyear{#1}}
\def\@revyyear{1973}
\def\@revyname{DIKUrevy}
\def\@title{En sketch}
\newif\if@author\@authorfalse
\newif\if@status\@statusfalse
\newif\if@eta\@etafalse
\newif\if@responsible\@responsiblefalse
\newif\if@melody\@melodyfalse
\def\author#1{\def\@author{#1}\@authortrue}
\def\status#1{\def\@status{#1}\@statustrue}
\def\eta#1{\def\@eta{#1}\@etatrue}
\def\responsible#1{\def\@responsible{#1}\@responsibletrue}
\def\melody#1{\def\@melody{#1}\@melodytrue}
\def\@author{}
\def\@status{}
\def\@eta{}
\def\@responsible{}
\def\@melody{}
\let\auteurs\author
\def\writtenbyname#1{\def\@writtenbyname{#1}}
\def\melodyname#1{\def\@melodyname{#1}}
\def\responsibletext#1{\def\@responsibletext{#1}}
\def\statustext#1{\def\@statustext{#1}}
\def\@writtenbyname{skrevet af}
\def\@melodyname{Melodi:}
\def\@responsibletext{\TeX--ansvarlig:}
\def\@statustext{Status:}
\newcommand{\pagessum}[1]{#1 side\ifnum1=#1\else r\fi}
\def\maketitle{{\thispagestyle{empty}
  \vspace*{-\headheight}\vspace*{-\headsep}
  \centering{\Large\@revyname{} \@revyyear}\vspace{5pt}\\
  {\LARGE \bf \@title}\vspace{5pt}\\
  \if@author{\large\@writtenbyname{} \@author}\vspace{5pt}\\\fi
  \if@melody{\sl\@melodyname{} \@melody}\vspace{5pt}\\\fi
  \if@leftfields
    \begin{varwidth}[t]{\bigheaderwidth}\raggedleft
      \if@status{\@statustext{} \@status}\vspace{2pt}\\\fi
      \if@responsible{\@responsibletext{} \@responsible}\vspace{2pt}\\\fi
      \if@eta{(\@eta)}\\\fi
    \end{varwidth}%
    \ \hspace{.5em}\vrule{}\hspace{.5em}
    \begin{varwidth}[t]{\smallheaderwidth}\raggedright
      Version \@version\vspace{2pt}\\
      \today\vspace{2pt}\\
      \pagessum{\getpagerefnumber{lastpage}}
    \end{varwidth}
  \else
    Version \@version
    \ \hspace{.5em}\vrule\hspace{.5em}
    \today
    \ \hspace{.5em}\vrule\hspace{.5em}
    \pagessum{\getpagerefnumber{lastpage}}
  \fi
  \vskip 5pt }}
\RequirePackage{varwidth}
\RequirePackage{refcount}
\def\if@leftfields{
  \def\@responsiblenum{\ifx\iftrue\if@responsible 1 \else 0 \fi}
  \def\@statusnum{\ifx\iftrue\if@status 1 \else 0 \fi}
  \def\@etanum{\ifx\iftrue\if@status 1 \else 0 \fi}
  \ifnum1=\ifnum1=\@responsiblenum 1
    \else \ifnum1=\@statusnum 1
    \else \ifnum1=\@etanum 1
    \else 0
  \fi\fi\fi
}
\newlength{\smallheaderwidth}
\setlength{\smallheaderwidth}{22ex}
\newlength{\bigheaderwidth}
\setlength{\bigheaderwidth}{\textwidth}
\addtolength{\bigheaderwidth}{-\smallheaderwidth}
\addtolength{\bigheaderwidth}{-1.5em}
\gdef\ps@revyheadings{
  \def\@oddhead{\vbox to 0pt{\vss
      \hbox to \textwidth{\hfil\rectoheaderthumbtab}
      \hbox{\rm\strut\@revyname{} \@revyyear}
      \hbox to \textwidth{Version \@version\quad\today
        \hfil {\large\sl\@title}\hfil
        Side \rm\thepage/\pageref{lastpage}}
      \hrule}}
  \def\@evenhead{\vbox to 0pt{\vss
      \hbox{\versoheaderthumbtab}
      \hbox to \textwidth{\hfil\rm\strut\@revyname{} \@revyyear}
      \hbox to \textwidth{Side \rm\thepage/\pageref{lastpage}
        \hfil {\large\sl\@title}\hfil
        Version \@version\quad\today}
      \hrule}}
  \def\@oddfoot{}\def\@evenfoot{}}
\newcommand{\rectoheaderthumbtab}{%
  \if@thumbindex
    \rectothumbtabfor{\@title}%
    \vspace*{ -\paperheight }\vspace*{ -\voffset }\vspace*{ 0.32in }%
    \hspace{-\paperwidth }\hspace{ 1in }\hspace{ \oddsidemargin }%
    \hspace{ \hoffset }\hspace{ \textwidth }\hspace{-.6cm}%
  \fi
}
\newcommand{\versoheaderthumbtab}{%
  \if@thumbindex
    \hspace{ -2.5in }\hspace{ -\evensidemargin }%
    \hspace{ -\hoffset }\hspace{ -1in }%
    \versothumbtabfor{\@title}%
    \vspace*{ -\paperheight }\vspace*{ -\voffset }\vspace*{ 0.32in }%
  \fi
}
\pagestyle{revyheadings}
\gdef\ps@empty{
  \def\@oddhead{\vbox to 0pt{\vss
      \hbox to \textwidth {\hfil\rectoheaderthumbtab }
      \vbox to 2em{}}}
  \def\@evenhead{\vbox to 0pt{\vss\hbox{\versoheaderthumbtab}}}
  \def\@oddfoot{}\def\@evenfoot{}}
\newenvironment{revy@list}[1]%
{{\smallskip\noindent\Large\bf#1}
  \begin{list}{}{
      \labelwidth 8em
      \leftmargin 10em
      \rightmargin 0em
      \labelsep 1em
      \listparindent 0em
      \topsep 1ex
      \partopsep 0ex
      \parsep 1ex
      \itemsep -1ex\relax
    }%
  }%
  {\end{list}\smallskip\hfil\rule{6cm}{0.1mm}\medskip\par}
\def\revy@itemname#1{%
  \def\@itemwithout##1{\item [{\bf ##1} \hfill] }
  \def\@itemwith##1[##2]{\item [{\bf ##1} (##2) \hfill] }
  \expandafter\def\csname #1\endcsname##1{%
    \@ifnextchar [{\@itemwith{##1}}{\@itemwithout{##1}}%]
  }
}
\newenvironment{roles}{
  \begin{revy@list}{\@rolename}
    \revy@itemname{role}
 }{
  \end{revy@list}
}
\newenvironment{props}{
  \begin{revy@list}{\@propname}
    \revy@itemname{prop}
 }{
  \end{revy@list}
}
\newenvironment{mics}{
  \begin{revy@list}{\@micname}
    \revy@itemname{mic}
 }{
  \end{revy@list}
}
\newenvironment{instructors}{
  \begin{revy@list}{\@instructorname}
    \def\@instructorwith[##1]{\item [{\bf ##1} \hfill] }
    \def\@instructorwithout{\item}
    \def\instructor{%
      \@ifnextchar [{\@instructorwith}{\@instructorwithout}%]
    }
 }{
  \end{revy@list}
}
\def\rolename#1{\def\@rolename{#1}}
\def\propname#1{\def\@propname{#1}}
\def\micname#1{\def\@micname{#1}}
\def\instructorname#1{\def\@instructorname{#1}}
\def\@rolename{Roller:}
\def\@propname{Rekvisitter:}
\def\@micname{Mikrofoner:}
\def\@instructorname{Instruktører:}
\newenvironment{sketch}{%
  \begin{revy@bodycommon}
  \rm\begin{list}{}{
      \labelwidth 2em
      \leftmargin 3em
      \rightmargin 0em
      \labelsep 0.5em
      \listparindent 2em
      \topsep 1ex
      \partopsep 1ex
      \parsep 0ex
      \itemsep 1ex\relax}%
  \item \rule{0.2em}{0em}\vspace{-1em}\par %}
  \newdimen\old@leftskip
  \old@leftskip \leftskip
  \newdimen\short@leftskip
  \short@leftskip \leftskip
  \advance\short@leftskip -1.5em
\def\says##1{\@ifnextchar [{\@saysas{##1}}{\@says{##1}}} %]
\def\@saysas##1[##2]{\rm\item [{\bf ##1 }{\it (##2)\,}\hfill:]
  \leftskip \old@leftskip}
\def\@says##1{\rm\item [{\bf ##1\,}\hfill:]\leftskip \old@leftskip}
\def\scene{\medskip\par\noindent\it\leftskip \short@leftskip }
  }{%
  \end{list}
  \end{revy@bodycommon}
}
\newenvironment{song}{%
  \begin{revy@bodycommon}
  \rm\begin{list}{}{%
      \raggedright
      \labelwidth 4.5em
      \leftmargin 7em
      \rightmargin 0em
      \labelsep 2em
      \listparindent -2em
      \topsep 0ex
      \partopsep \bigskipamount
      \parsep .6\baselineskip
      \itemsep -.6\baselineskip
      \relax
    }
  \item[] \rule{0.2em}{0em}\vspace{-\baselineskip}\strut\par %}
  \newdimen\old@leftskip
  \old@leftskip \leftskip
  \newdimen\short@leftskip
  \short@leftskip \leftskip
  \advance\short@leftskip -5.5em
\def\sings##1{\obeycr
  \@ifnextchar [{\@singsas{##1}}{\@sings{##1}}} %}
\def\@singsas##1[##2]{\rm\item [\hskip\@leftsingpad{\bf ##1 }{\it
    (##2)\,}:\hskip\@rightsingpad]\hskip-2em\leftskip \old@leftskip}
\def\@sings##1{\rm\item [\hskip\@leftsingpad{\bf ##1\,}:\hskip
  \@rightsingpad]\hskip-2em\leftskip \old@leftskip}
\let\old@sings=\sings
\def\scene{%
  \def\sings{\let\sings=\old@sings \medskip\sings}
  \medskip\par\leftskip \short@leftskip \restorecr
  \it\noindent\relax
}
  \newskip\@leftsingpad
  \newskip\@rightsingpad
  \def\flushsingsright{\@leftsingpad 0pt plus 1fill\@rightsingpad 0pt\relax}
  \def\flushsingsleft{\@leftsingpad 0pt\@rightsingpad 0pt plus 1fill\relax}
  \flushsingsleft
  \tolerance10000\hfuzz21cm\obeycr
}{
  \end{list}
  \end{revy@bodycommon}
}
\newif\if@newpar
{
  \catcode`\^^M=13
  \gdef\@carriagereturn{%
    \@ifnextchar^^M{%
      \@newpartrue%
    }{%
      \@ifnextchar\end{}{%
        \@ifnextchar\sings{%
          \if@newpar\bigskip\par\fi\@newparfalse%
        }{%
          \if@newpar\par\else\\\fi\@newparfalse%
        }%
      }%
    }%
  }%
  \gdef\obeycr{%
    \catcode`\^^M=13 %
    \let^^M=\@carriagereturn%
    \@gobblecr%
  }%
  \gdef\restorecr{\catcode`\^^M=5 }%
}
\newenvironment{revy@bodycommon}{
  \let\role = \textbf
  \def\does##1{\scene \hspace{-1em}\role{##1}}
  \def\act##1{\textit{(##1)}}
}{}
\let\revyinfo=\relax
\newtoks\@titletoks
\newtoks\@authortoks
\newtoks\@melodytoks
\newtoks\@revyrevynametoks
\newtoks\@revyrevyyeartoks
\let\end@document=\enddocument
\def\enddocument{\label{lastpage}\write\@auxout
  {\string\@ifundefined{revyinfo}{\string\def\string
  \revyinfo\string##1\string##2\string##3\string
  ##4\string##5\string##6\string##7\string##8{}}{}}\@titletoks=
  \expandafter{\@title}\@titletoks=
  \expandafter{\@title}\@authortoks=
  \expandafter{\@author}\@melodytoks=
  \expandafter{\@melody}\@revyrevynametoks=
  \expandafter{\@revyname}\@revyrevyyeartoks=
  \expandafter{\@revyyear}\write\@auxout
  {\string\revyinfo{\the\@titletoks}{\@version}
    {\today}%
    {\the\@authortoks}%
    {\the\@melodytoks}%
    {}%
    {\the\@revyrevynametoks}%
    {\the\@revyrevyyeartoks}%
  }%
  \end@document
}
\endinput
%%
%% End of file `ucph-revy.cls'.
