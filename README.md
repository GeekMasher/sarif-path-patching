# sarif-path-patching

SARIF Relative Path Patching Tool/Action

## Usage

### Actions

```yaml
- uses: GeekMasher/sarif-path-patching@main
  with:
    # Set the Root directory 
    # [optional]: Default: '../results'
    root: '..'
    # SARIF File / Directory location
    # [optional]
    sarif: 'sarif-output.json'

```
