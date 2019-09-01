# configkit

Easy to use versioned config files for Python

## Usage

```python
from configkit import SchemaDirectory

# Tell where to find your versioned schemas
schema_directory = SchemaDirectory("/path/to/json/schemas")

# Use the latest "config" schema to load a config file
config = schema_directory["config"].latest().load("/path/to/config.json")

# Or get a compatible version of a schema, and use
# that to load the file
credentials = schema_directory["credentials"].version("~=11.1.0").load("/path/to/credentials.json")
```
