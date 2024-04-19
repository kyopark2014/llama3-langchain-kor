FROM amazon/aws-lambda-python:3.11

WORKDIR /var/task/lambda-chat

COPY lambda_function.py /var/task/
COPY test.py /var/task/   
COPY . ..

RUN /var/lang/bin/python3.11 -m pip install --upgrade pip

RUN /var/lang/bin/python3 -m pip install PyPDF2
RUN /var/lang/bin/python3 -m pip install langchain
RUN /var/lang/bin/python3 -m pip install langchain-community
RUN /var/lang/bin/python3 -m pip install unstructured
RUN /var/lang/bin/python3 -m pip install anthropic
RUN /var/lang/bin/python3 -m pip install python-pptx
RUN /var/lang/bin/python3 -m pip install python-docx

RUN /var/lang/bin/python3 -m pip install botocore --upgrade
RUN /var/lang/bin/python3 -m pip install boto3 --upgrade

CMD ["lambda_function.lambda_handler"]