# Publitio Python SDK

Installation:

```
pip install publitio
```

To use the Python SDK:

```
from publitio import PublitioAPI
publitio_api = PublitioAPI(key='xxxx', secret='yyyy')
```

For the remaning code samples, these two lines of code will be implied.

The methods used for communicating with the api - `create_file`, `list_files` etc., all return parsed json responses, as if `json.loads` was used on the response content. The only exception to this is the `transformed` method, which returns `bytes`. In all methods, the supported keyword parameters are exactly the same as in the publitio docs: https://publit.io/docs. You should probably look into that documentation before reading this.


## Exceptions
 - `UnknownStatusCode` - raised when the server responds to a request with an unknown status code.
 - `TransformationFailed` - raised when the server fails to perform a transformation, i.e. when `publitio_api.transform` fails.

## Transforming files
```
publitio_api.transformed('filename.jpeg', extension='png', w=300, h=300)
```

This would return the `bytes` of the file named `filename`, now transcoded into a PNG, with dimensions 300x300. The supported parameters are the same as in https://publit.io/docs/#url-based-transformations. For example, the above invocation makes a call to this URL:
```
https://media.publit.io/file/w_300,h_300/filename.png
```


## Creating files
```
publitio_api.create_file(file=open('path/to/file', 'rb'),
                         title='My title',
                         description='My description')
```
Please do note that the file must be opened for binary reading. **The `publitio_api.create_file` function will not close the file**. Therefore, what you will probably want to do most of the time is:
```
with open('path/to/file', 'rb') as f:
    publitio_api.create_file(file=open('path/to/file', 'rb'),
                             title='My title',
                             description='My description')
```


## Listing files
```
publitio_api.list_files(offset=1, ...)
```

It's also OK to provide strings as parameters when numbers seem logical. So, also valid:

```
publitio_api.list_files(offset='1', ...)
```


## Showing files
```
publitio_api.show_file(file_id)
```


## Updating files
```
publitio_api.update_file(file_id, title='A better title', ...)
```


## Deleting files
```
publitio_api.delete_file(file_id)
```


## Getting a file player
```
publitio_api.get_file_player(file_id, player='myplayerid', ...)
```


## Creating file versions
```
publitio_api.create_version(file_id, extension='.webm', ...)
```


## Listing versions
```
publitio_api.list_versions(file_id, limit=3)  # Or limit='3'
```


## Showing versions
```
publitio_api.show_version(version_id)
```


## Deleting versions
```
publitio_api.delete_version(version_id)
```


## Creating players
```
publitio_api.create_player(name='whatever', ...)
```


## Listing players
```
publitio_api.list_players()
```


## Showing players
```
publitio_api.show_player(player_id)
```


## Updaing players
```
publitio_api.update_player(player_id, skin='green', ...)
```


## Deleting players
```
publitio_api.delete_player(player_id)
```


## Creating adtags
```
publitio_api.create_adtag(name='name', tag='tag')
```


## Listing adtags
```
publitio_api.list_adtags()
```


## Showing adtags
```
publitio_api.show_adtag(adtag_id)
```


## Updating adtags
```
publitio_api.update_adtag(adtag_id, tag='newtag')
```


## Deleting adtags
```
publitio_api.delete_adtag(adtag_id)
```


## Creating a watermark
```
publitio_api.create_watermark(self, file=open('path/to/file', rb), title='whatever')
```
Again, the file needs to be opened for binary reading. This function will not close the file.


## Listing watermarks
```
publitio_api.list_watermarks()
```

## Showing watermarks
```
publitio_api.show_watermark(watermark_id)
```


## Updating watermarks
```
publitio_api.update_watermark(watermark_id, position='left', ...)
```

## Deleting watermarks
```
publitio_api.delete_watermark(watermark_id)
```
