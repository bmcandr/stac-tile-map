FROM public.ecr.aws/lambda/python:3.8

# Install the function's dependencies using file requirements.txt
# from your project folder.

COPY requirements-pip.txt  .
RUN  pip3 install -r requirements-pip.txt --target "${LAMBDA_TASK_ROOT}"

# Copy function code
COPY src ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "src.python.api.magnum_handler.handler" ]