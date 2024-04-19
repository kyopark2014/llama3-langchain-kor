# Llama3와 LangChain을 이용하여 한국어 Chatbot 만들기

여기서는 LLM으로 Llama3를 이용하여 한국어 Chatbot을 만드는 것을 설명합니다. 개발은 LangChain을 활용하였습니다. 전체적인 Architecture는 아래와 같습니다.

<img src="https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/76825d03-fde4-494f-85f1-8b50920edf77" width="800">

## 직접 실습 해보기

### 사전 준비 사항

이 솔루션을 사용하기 위해서는 사전에 아래와 같은 준비가 되어야 합니다.

- [AWS Account 생성](https://repost.aws/ko/knowledge-center/create-and-activate-aws-account)에 따라 계정을 준비합니다.

### CDK를 이용한 인프라 설치

본 실습에서는 Seoul 리전 (ap-northeast-2)을 사용합니다. [인프라 설치](./deployment.md)에 따라 CDK로 인프라 설치를 진행합니다. [CDK 구현 코드](./cdk-multimodal-and-rag/README.md)에서는 Typescript로 인프라를 정의하는 방법에 대해 상세히 설명하고 있습니다. 

## 실행결과

![image](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/7e01dc96-5f27-400e-a25f-b094e245e391)

## 리소스 정리하기 

더이상 인프라를 사용하지 않는 경우에 아래처럼 모든 리소스를 삭제할 수 있습니다. 

1) [API Gateway Console](https://us-west-2.console.aws.amazon.com/apigateway/main/apis?region=us-west-2)로 접속하여 "rest-api-for-llama3-langchain-kor", "ws-api-for-llama3-langchain-kor"을 삭제합니다.

2) [Cloud9 Console](https://us-west-2.console.aws.amazon.com/cloud9control/home?region=us-west-2#/)에 접속하여 아래의 명령어로 전체 삭제를 합니다.


```text
cd ~/environment/llama3-langchain-kor/cdk-llama3-korg/ && cdk destroy --all
```

## 결론

LangChain을 이용하여 Llama3로 한국어 Chatbot을 만들었습니다. 현재까지 테스트시에는 Llama2에서는 전혀 지원되던 한국어가 괜찮은 성능으로 제공되고 있습니다. 추가 테스트를 통해 활용방안을 확인할 예정입니다.
