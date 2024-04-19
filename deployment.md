# 인프라 설치하기

## Llama3 설치하기

[SageMaker-Oregon](https://us-west-2.console.aws.amazon.com/sagemaker/home?region=us-west-2#/studio-landing)에 접속해서 SageMaker Studio에서 아래와 같이 Llama3를 설치합니다. 자세한 내용은 [Meta Llama 3 models](https://aws.amazon.com/ko/blogs/machine-learning/meta-llama-3-models-are-now-available-in-amazon-sagemaker-jumpstart/)을 참조합니다. 

![image](https://github.com/kyopark2014/llama3-langchain-rag/assets/52392004/7aa5db7e-c8aa-4f27-9c77-19b561e1426a)

Meta-Llama-3-8B-Instruct을 선택하면, ml.g5.12xlarge가 기본값으로 선택됩니다. Deploy를 선택하면 아래와 같이 "jumpstart-dft-meta-textgeneration-llama-3-8b-instruct"라는 이름으로 SageMaker Endpoint가 설치됩니다. 

![image](https://github.com/kyopark2014/llama3-langchain-rag/assets/52392004/2aa02d81-b7c6-473c-a1e9-a6070453e42f)

Llama3가 설치가 되면 AWS CDK를 이용하여 필요한 인프라를 설치합니다.


## CDK를 이용한 인프라 설치하기

여기서는 [AWS Cloud9](https://aws.amazon.com/ko/cloud9/)에서 [AWS CDK](https://aws.amazon.com/ko/cdk/)를 이용하여 인프라를 설치합니다. 또한 편의상 서울 리전을 통해 실습합니다.

1) [Cloud9 Console](https://ap-northeast-2.console.aws.amazon.com/cloud9control/home?region=ap-northeast-2#/create)에 접속하여 [Create environment]-[Name]에서 “chatbot”으로 이름을 입력하고, EC2 instance는 “m5.large”를 선택합니다. 나머지는 기본값을 유지하고, 하단으로 스크롤하여 [Create]를 선택합니다.

![image](https://github.com/kyopark2014/demo-ai-dansing-robot/assets/52392004/807e3712-d98f-4359-9c79-0ea8359861ea)

2) [Environment](https://ap-northeast-2.console.aws.amazon.com/cloud9control/home?region=ap-northeast-2#/)에서 “chatbot”를 [Open]한 후에 아래와 같이 터미널을 실행합니다.

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
cdk bootstrap aws://[account-id]/ap-northeast-2
```

8) 아래 명령어로 인프라를 설치합니다.

```java
cdk deploy --all
```

인프라가 설치가 되면 아래와 같은 Output을 확인할 수 있습니다. 여기에서는 접속하는 URL인 WebUrlforstreamchatbot과 CloudFront 주소를 distributionDomainNamefordemodansingrobotl로 알 수 있습니다.


![image](https://github.com/kyopark2014/demo-ai-dansing-robot/assets/52392004/f39623bc-6574-4e62-abfd-b0605d42436c)

9) NAT 설정

[VPC Console](https://ap-northeast-2.console.aws.amazon.com/vpcconsole/home?region=ap-northeast-2#vpcs:)에 접속합니다.

아래와 같이 "vpc-for-llama3-langchain-kor"의 VPC ID를 선택합니다. 

![image](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/764dd596-c8b9-4c89-80c5-ba612d5829a7)

아래와 같이 subnet중에 private를 찾아서 Route tables을 선택합니다. Subnets에서 public/private 이름을 가진 2개의 subnet이 있으므로 private을 주의하여 선택합니다. 

![noname](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/cbf27381-9c73-460d-89eb-0682d5bea066)

[Routs]에서 [Edit routes]를 선택합니다.

![noname](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/047be27b-0518-475a-ba9a-a9fe3e781cc2)

아래와 같이 [Add route]를 선택하여, Destionation으로 "0.0.0.0/0"을 선택하고, Target은 "Nat Gateway"를 선택하여 생성되어 있는 NAT를 지정합니다. 이후 [Save changes]를 선택하여 저장합니다. 

![noname](https://github.com/kyopark2014/llama3-langchain-kor/assets/52392004/a03e9e9e-b49b-4210-96d3-c0c1cd0f3493)

10) Output의 WebUrlforstreamchatbot의 URL로 접속합니다. Voice Interpreter와 사용자 ID를 이용해 데이터를 교환합니다. 따라서 사용자 ID로 "robot"라고 입력합니다.

## Voice Interpreter 

Voice Interpreter는 음성으로부터 Text를 추출합니다. 이때 [Amazon Transcribe Streaming SDK](https://github.com/awslabs/amazon-transcribe-streaming-sdk)을 활용하였습니다. 아래를 실행하기 전에 requirements를 설치합니다.

```text
pip install -r requirements.txt
```

interpreter 폴더로 이동하여, [config.ini](./interpreter/config.ini) 파일을 연 후에 아래의 내용을 업데이트 합니다. url은 Output의 distributionDomainNamefordemodansingrobotl의 주소로 업데이트 합니다.

```text
[system]
url = https://d1r17qhj4m3dnc.cloudfront.net/redis
userId = robot
```

이후 아래와 같이 실행합니다.

```text
python mic_main.py
```
