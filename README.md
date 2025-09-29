# Sade Wiki
A lightweight wiki system written in Python, taking advantage of the Github API. Designed for use cases such as D&D campaigns or podcasts.

SadeWiki is a GitHub action, it looks around the local directory for markdown files and converts them into HTML. Once done, these can be uploaded as an artifact and hosted on a GitHub pages site.

Example usage:
```yaml
name: Build HTML

# Controls when the workflow will run
on:
  push:
    branches: [ "main" ]

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4 # Check out source so we can work on it
      - name: Build
        uses: hinkleydev/SadeWiki@v0 # Build wiki
      - name: Upload Build Artifacts
        uses: actions/upload-pages-artifact@v3 # Upload built site
        with:
          path: ${{ github.workspace }}/docs
          name: wiki
          
  deploy:
    needs: build
    runs-on: ubuntu-latest
    
    permissions:
      pages: write      # to deploy to Pages
      id-token: write   # to verify the deployment originates from an appropriate source
      
    steps:
      - name: Deploy to GitHub Pages # Upload the artifact
        uses: actions/deploy-pages@v4
        with:
          artifact_name: wiki
```

## How to get started
The easiest way to get started is to clone the [template repo](https://github.com/hinkleydev/SadeWiki-template), this includes the workflow YAML and a basic HTML file explaining how to get started.
