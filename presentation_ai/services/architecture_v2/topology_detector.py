import re

VALID_TOPOLOGIES = {
    "layered", "microservices", "cloud", "event_driven", 
    "star", "ring", "hub_spoke", "kubernetes", 
    "ai_pipeline", "transformer", "cnn", "uml", "flowchart"
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
        return "layered" # default fallback
        
    # Auto mode: scan topic using regex/keyword matching
    topic_lower = topic.lower()
    
    if re.search(r'\b(netflix|microservice|microservices|soa|service-oriented)\b', topic_lower):
        return "microservices"
    elif re.search(r'\b(aws|gcp|azure|cloud|cloud-native|vpc|subnet|s3|ec2)\b', topic_lower):
        return "cloud"
    elif re.search(r'\b(kafka|event|events|event-driven|pubsub|publisher|subscriber|mq|rabbitmq|activemq|stream|streaming)\b', topic_lower):
        return "event_driven"
    elif re.search(r'\b(kubernetes|k8s|docker|container|containers|pod|pods|helm|cluster)\b', topic_lower):
        return "kubernetes"
    elif re.search(r'\b(chatgpt|openai|agent|agents|llm|ai|ai-pipeline|pipeline|rag|langchain|ollama|model-training)\b', topic_lower):
        return "ai_pipeline"
    elif re.search(r'\b(transformer|transformers|attention|self-attention|bert|gpt|encoder|decoder)\b', topic_lower):
        return "transformer"
    elif re.search(r'\b(cnn|conv|convolutional|resnet|vgg|lenet|pooling|maxpool)\b', topic_lower):
        return "cnn"
    elif re.search(r'\b(uml|class-diagram|sequence-diagram|use-case)\b', topic_lower):
        return "uml"
    elif re.search(r'\b(flowchart|flow|workflow|process|steps|decision)\b', topic_lower):
        return "flowchart"
    elif re.search(r'\b(ring|loop|circular)\b', topic_lower):
        return "ring"
    elif re.search(r'\b(star|hub|spoke|hub-spoke)\b', topic_lower):
        return "star"
        
    # Default fallback for auto mode
    return "layered"
