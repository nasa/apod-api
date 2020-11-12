# apod_object_parser

get a Nasa api key by clicking <a href="https://api.nasa.gov/#signUp">here</a>.

## How to use
1. import the file
```python
import apod_object_parser
```
2. Now call the `get_data` function and pass the `nasa api key` as the argument. Note api_key is a string. The response returned will be a Dictionary. Now you can parse the dictionary too

```python 
response = apod_object_parser.get_data(##Pass In Your API key here)
```
### get_date

the `get_date` function takes the dictionary we got above and returns the date.

```python
date = apod_object_parser.get_date(response)
```
### get_explaination
the `get_explaination` function takes the dictionary we got above and returns the explaintion.

```python
date = apod_object_parser.get_explaination(response)
```
### get_hdurl
the `get_hdurl` function takes the dictionary we got above and returns the High Definition url of the image.

```python
date = apod_object_parser.get_hdurl(response)
```
### get_title
the `get_title` function takes the dictionary we got above and returns the title of the image.

```python
date = apod_object_parser.get_title(response)
```
### get_url
the `get_url` function takes the dictionary we got above and returns the Standard definition url of the image.

```python
date = apod_object_parser.get_hdurl(response)
```
### get_media_type
the `get_media_type` function takes the dictionary we got above and returns the media type the file (might be a video of a image).

```python
date = apod_object_parser.get_hdurl(response)
```

## Other functions
there are also other functions that might help you in situations

### download_image
the `download_image` finction takes the url (hdurl or url) and the date from the function `get_date` and downloads the image in the current directory and with the file name of the date. the image downloaded is in the .jpg format
```python
apod_object_parser.download_image(url, date)
```

### convert_image
sometimes the image we downloaded above might not be in the right format (.jpg) so you may call `convert_image` function to convert the image into .png. takes the `image_path` parameter which is the filepath.
```python 
apod_object_parser.convert_image(image_path)
```
