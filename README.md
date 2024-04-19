# llama3-langchain-rag
It shows a sample architecture deploying RAG on Llama3 based on LangChain.


## Error

```text
AttributeError: 'SageMakerRuntime' object has no attribute 'post_to_connection'
LAMBDA_WARNING: Unhandled exception. The most likely cause is an issue in the function code. However, in rare cases, a Lambda runtime update can cause unexpected function behavior. For functions using managed runtimes, runtime updates can be triggered by a function change, or can be applied automatically. To determine if the runtime has been updated, check the runtime version in the INIT_START log entry. If this error correlates with a change in the runtime version, you may be able to mitigate this error by temporarily rolling back to the previous runtime version. For more information, see https://docs.aws.amazon.com/lambda/latest/dg/runtimes-update.html
[ERROR] Exception: Not able to send a message
Traceback (most recent call last):
  File "/var/task/lambda_function.py", line 541, in lambda_handler
    sendMessage(connectionId, "__pong__")
  File "/var/task/lambda_function.py", line 272, in sendMessage
    raise Exception ("Not able to send a message")
```
