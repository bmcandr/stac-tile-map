FROM public.ecr.aws/lambda/python:3.9
# FROM python:3.9

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements-pip.txt  .
# RUN  pip3 install -r requirements-pip.txt --target "${LAMBDA_TASK_ROOT}"
RUN  pip3 install -r requirements-pip.txt

# Copy data directory
COPY data /geojson_data

# Copy function code
COPY src/python app

ENV PYTHONPATH=app

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "app.api.mangum_handler.handler" ]