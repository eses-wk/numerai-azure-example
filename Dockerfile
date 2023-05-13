# Reference: https://docs.docker.com/engine/reference/builder/

# Provides a working Python 3 environment.
FROM python:3.10.10

# Now, add everything in the source code directory.
# (including your subfolders, code, compiled files, serialized models, everything...)
ADD . .

# (Optional) you may put your Numerai keys here or load as .env file in the root directory
#ENV NUMERAI_PUBLIC_ID=XXXXXXXXXXXXXXXX
#ENV NUMERAI_SECRET_KEY=YYYYYYYYYYYYYYYY

# We added the requirements.txt file from above, now pip install every requirement from it.
# RUN is the command that will be run at build time
RUN pip install -r requirements.txt --no-cache-dir

# This sets the default command when your container instance starts
CMD [ "python", "./predict.py" ]