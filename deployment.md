# 인프라 설치하기

## Llama3 설치하기

[SageMaker-Oregon](https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio-landing)에 접속해서 SageMaker Studio에서 아래와 같이 Llama3를 설치합니다. 자세한 내용은 [Meta Llama 3 models](https://aws.amazon.com/ko/blogs/machine-learning/meta-llama-3-models-are-now-available-in-amazon-sagemaker-jumpstart/)을 참조합니다. 

![image](https://github.com/kyopark2014/llama3-langchain-rag/assets/52392004/7aa5db7e-c8aa-4f27-9c77-19b561e1426a)

Meta-Llama-3-8B-Instruct을 선택하면, ml.g5.12xlarge가 기본값으로 선택됩니다. Deploy를 선택하면 아래와 같이 "jumpstart-dft-meta-textgeneration-llama-3-8b-instruct"라는 이름으로 SageMaker Endpoint가 설치됩니다. 

![image](https://github.com/kyopark2014/llama3-langchain-rag/assets/52392004/2aa02d81-b7c6-473c-a1e9-a6070453e42f)

Llama3가 설치가 되면 AWS CDK를 이용하여 필요한 인프라를 설치합니다.


## CDK를 이용한 인프라 설치하기

여기서는 [AWS Cloud9](https://aws.amazon.com/ko/cloud9/)에서 [AWS CDK](https://aws.amazon.com/ko/cdk/)를 이용하여 인프라를 설치합니다. 또한 편의상 Oregon 리전을 통해 실습합니다.

1) [Cloud9 Console](https://us-west-2.console.aws.amazon.com/cloud9control/home?region=us-west-2#/create)에 접속하여 [Create environment]-[Name]에서 “chatbot”으로 이름을 입력하고, EC2 instance는 “m5.large”를 선택합니다. 나머지는 기본값을 유지하고, 하단으로 스크롤하여 [Create]를 선택합니다.

![image](https://github.com/kyopark2014/demo-ai-dansing-robot/assets/52392004/807e3712-d98f-4359-9c79-0ea8359861ea)

2) [Environment](https://us-west-2.console.aws.amazon.com/cloud9control/home?region=us-west-2#/)에서 “chatbot”를 [Open]한 후에 아래와 같이 터미널을 실행합니다.

![image](https://github.com/kyopark2014/demo-ai-dansing-robot/assets/52392004/314d1acf-e5f6-4ba5-810c-9bc06bb4ef03)

3) EBS 크기 변경

코드를 수정하면서 추가 빌드를 하게 되면 EBS 용량을 확대하는것이 편리합니다. 이를 위하여, 아래와 같이 스크립트를 다운로드 합니다. 

```text
curl https://raw.githubusercontent.com/kyopark2014/technical-summary/main/resize.sh -o resize.sh
```

이후 아래 명령어로 용량을 80G로 변경합니다.
```text
chmod a+rx resize.sh && ./resize.sh 80
```

4) 소스를 다운로드합니다.

```java
git clone https://github.com/kyopark2014/llama3-langchain-kor
```

5) cdk 폴더로 이동하여 필요한 라이브러리를 설치합니다.

```java
cd llama3-langchain-kor/cdk-llama3-kor/ && npm install
```

7) CDK 사용을 위해 Boostraping을 수행합니다.

아래 명령어로 Account ID를 확인합니다.

```java
aws sts get-caller-identity --query Account --output text
```

아래와 같이 bootstrap을 수행합니다. 여기서 "account-id"는 상기 명령어로 확인한 12자리의 Account ID입니다. bootstrap 1회만 수행하면 되므로, 기존에 cdk를 사용하고 있었다면 bootstrap은 건너뛰어도 됩니다.

```java
cdk bootstrap aws://[account-id]/us-west-2
```

8) 아래 명령어로 인프라를 설치합니다.

```java
cdk deploy --all
```

인프라가 설치가 되면 아래와 같은 Output을 확인할 수 있습니다. 여기에서는 접속하는 URL인 WebUrlforllama3langchainkor로 알 수 있습니다.

![noname](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/2a28c2ca-294f-4374-a099-da124d84e485)

9) WebUrlforllama3langchainkor로 접속하여 "demo"라고 id를 넣고, "General Conversation"으로 입력후 Submit을 선택합니다. User Id로 대화이력이 저장되므로 여러명이 접속할 경우에는 다른 이름을 사용합니다.

![image](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/dfccc134-e731-41cb-b78a-d111ed742244)

    
