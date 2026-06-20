import re

VALID_TOPOLOGIES = {
    "microservices", "cloud", "kubernetes", "ai_pipeline", 
    "rag_pipeline", "event_driven", "transformer", "cnn", 
    "mvc", "hexagonal", "layered", "client_server"
}

def detect_topology(architecture_type: str, topic: str = "") -> str:
    """
    Detects and returns the target topology string.
    If architecture_type is 'auto', determines the best layout based on keywords in the topic.
    Otherwise, returns the selected type if valid, falling back to 'layered'.
    """
    if not architecture_type or architecture_type == "none":
        return "none"
        
    arch_type = architecture_type.lower().strip()
    
    if arch_type != "auto":
        if arch_type in VALID_TOPOLOGIES:
            return arch_type
        # Some alias mapping
        if arch_type == "aws" or arch_type == "gcp" or arch_type == "azure":
            return "cloud"
        return "layered" # default fallback
        
    # Auto mode: scan topic using regex/keyword matching
    topic_lower = topic.lower()
    
    # 1. RAG
    if re.search(r'\b(rag|vector-db|pinecone|embedding|chunker|retriever|document-loader|similarity-search|knowledge-base)\b', topic_lower):
        return "rag_pipeline"
    # 2. AI / Chatbot
    elif re.search(r'\b(chatgpt|openai|agent|agents|llm|ai|ai-pipeline|pipeline|langchain|ollama|model-training|guardrails|prompt-builder|response-api|chatbot)\b', topic_lower):
        return "ai_pipeline"
    # 3. Docker / Client-Server
    elif re.search(r'\b(docker|dockerfile|docker-compose|daemon|containerization)\b', topic_lower):
        return "client_server"
    # 4. Kubernetes
    elif re.search(r'\b(kubernetes|k8s|pod|pods|ingress|deployments|persistent-volume|configmap|helm|cluster)\b', topic_lower):
        return "kubernetes"
    # 5. Cloud
    elif re.search(r'\b(aws|gcp|azure|cloud|cloud-native|vpc|subnet|s3|ec2|load-balancer|region)\b', topic_lower):
        return "cloud"
    # 6. Event Driven
    elif re.search(r'\b(kafka|event|events|event-driven|pubsub|publisher|subscriber|mq|rabbitmq|activemq|stream|streaming|broker)\b', topic_lower):
        return "event_driven"
    # 7. Netflix / Microservices
    elif re.search(r'\b(netflix|microservice|microservices|soa|service-oriented|auth-service|catalog-service)\b', topic_lower):
        return "microservices"
    # 8. Transformer
    elif re.search(r'\b(transformer|transformers|attention|self-attention|bert|gpt|encoder|decoder)\b', topic_lower):
        return "transformer"
    # 9. CNN
    elif re.search(r'\b(cnn|conv|convolutional|resnet|vgg|lenet|pooling|maxpool)\b', topic_lower):
        return "cnn"
    # 10. MVC
    elif re.search(r'\b(mvc|model-view-controller|controller|view)\b', topic_lower):
        return "mvc"
    # 11. Hexagonal
    elif re.search(r'\b(hexagonal|ports-and-adapters|port|adapter|clean-architecture)\b', topic_lower):
        return "hexagonal"
    # 12. Client-Server general keywords
    elif re.search(r'\b(client-server|socket|web-server|http-connection)\b', topic_lower):
        return "client_server"
        
    return "layered"
