# ESNcards generator

This tools serves help for ESN members to mass produce ESNcards, it gets input data from `.csv` file downloaded from Application Google Form, downloads uploaded photos of applications, and generates `.pdf` as print resources. 

## How to produce cards
### Installation
Install all requirements into your python3 enviroment -- all listed in `requirements.txt`.

### Download data from gForm
Download form responses in .csv format, expected headers:

* `Timestamp`in ISO format
* `Email`
* `Name and Surname  (e.g. Walter White)`
* `Country (e.g. Mexico)`
* `Date of Birth (e.g. 07/09/98)`
* `Upload a passport-sized photo of yourself (2.7x3.7 cm)` as google drive link
* `__dummy__`
* `__dummy__`
* `Who exactly recommend you to apply for ESNcard, where did you find out about it?`
* `Do you need it before your arrival in Brno?`

### Download photos

File `client_secret.json` (placed in project root) is needed to access Google Drive, you can get one from
[Google APIs](https://console.developers.google.com/apis/credentials), especially
OAuth 2.0
Client IDs (with all Google Drive perms) for your own project.

Then run the following command:

```
./download_images.py <downloaded_form_file>.csv
```

In case of unknown format, photo is stored in project root. Before next steps, it's needed to reformat the file and move into `pictures` directory under the same name.

### Generating ESNcard print files

Help:
```
usage: generate.py [-h] [-i IMGPATH] [-p PEOPLECSV] [-o OUTPUT] [-m {photo,text,all}] [-d {normal,reversed}] [-e {clahe,heq_yuv,heq_hsv,other}] [-c] [--interactive]

optional arguments:
  -h, --help            show this help message and exit
  -i IMGPATH, --imgpath IMGPATH
                        Folder with images to be processed. (default: pictures)
  -p PEOPLECSV, --peoplecsv PEOPLECSV
                        CSV file with students and their details. (default: students.csv)
  -o OUTPUT, --output OUTPUT
                        Output file. (default: output-<mode>.pdf)
  -m {photo,text,all}, --mode {photo,text,all}
                        Printing mode. (default: all)
  -d {normal,reversed}, --direction {normal,reversed}
                        Printing direction: normal - TOP -> BOTTOM, reversed - BOTTOM -> TOP (default: normal)
  -e {clahe,heq_yuv,heq_hsv,other}, --equalizehist {clahe,heq_yuv,heq_hsv,other}
                        Equalize histogram. Modes: clahe - Contrast Limited Adaptive Histogram Equalization, heq_yuv - Global Histogram Equalization (YUV), heq_hsv - Global Histogram Qqualization (HSV), other - Placeholder for tests. (default: None)
  -c, --crop            Crop images using face detection. (default: False)
  --interactive         Ask which image to use each time - original, or cropped. (default: False)

```

So the typical usage would be:

To check all photos are fine and data is loaded properly, output is `output-all.pdf`:
```
./generate.py --mode all
```
To render just labels to print them on transparent foil, output is `output-text.pdf`:
```
./generate.py --mode text
```

To render just photos to print, output is `output-photo.pdf`:
```
./generate.py --mode photo
```

## Authors
* IT department of ESN VUT Brno:
* [Jozef Zuzelka](https://github.com/jzlka)
* [Joe Kolář](https://github.com/thejoeejoee)

## Sample outputs

![all-1](https://user-images.githubusercontent.com/6154740/153076972-c37f52de-cd6a-4b7f-a978-19f92f68c1d0.png)
![photo-1](https://user-images.githubusercontent.com/6154740/153076979-541d7e68-5330-43c3-9e46-b239153d04d4.png)
![text-1](https://user-images.githubusercontent.com/6154740/153076981-f09c691d-9944-4cb4-8804-a5072b7aff59.png)
