A minimalistic offline Python Console App for PDF utilities. Includes
- Reduce PDF
- Extract Pages
- Merge PDFs in Box

How to run?
- Clone the repository
```
https://github.com/aaniksahaa/hello-pdf.git
```
- Install the requirements
```
pip install -r requirements.txt
```
- Then double-click on run.bat

Please note that,
- Reduce PDF
    - The pdf must be in the current directory
    - Consecutive pages will be checked against redundancy, and if found, redundant pages will be removed
    - Helpful for pdfs formatted with LaTeX beamer
- Extract Pages
    - The pdf must be in the current directory
    - Page range will be extracted as new pdf
- Merge PDF
    - The pdfs must be in the box directory
    - You need to name the files such that thay appear in your desired order
    - Numbering them sequentially 1,2,3... (something like '1-abc.pdf','2-xyz.pdf',etc...) will do
