FROM node:25-slim

# Install dummy xdg-open to prevent crash when tool tries to open browser
RUN echo '#!/bin/sh' > /usr/local/bin/xdg-open && chmod +x /usr/local/bin/xdg-open

WORKDIR /app

# Install the package
RUN npm install @microsoft/m365agentsplayground

# Expose any ports if needed (the playground might run a web server internally for the UI)
EXPOSE 3000

# Set the entrypoint to the agentsplayground binary
ENTRYPOINT ["/app/node_modules/.bin/agentsplayground"]

# CMD is handled by the Makefile
