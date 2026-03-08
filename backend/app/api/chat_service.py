import os
import json
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

app_dir = Path(__file__).resolve().parents[1]
backend_dir = app_dir.parent
load_dotenv(app_dir / ".env")
load_dotenv(backend_dir / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY") or None)

def _entity_name(entity: dict) -> str:
    if not isinstance(entity, dict):
        return ""
    return str(
        entity.get("name")
        or entity.get("entity_name")
        or entity.get("label")
        or ""
    ).strip()

async def agent1_extract_entities(text: str) -> dict:
    """Extract ONLY entities - no relations"""
    
    prompt = f"""Extract ONLY entities from this message. Just names, places, concepts.

Message: "{text}"

JSON:
{{
    "entities": [
        {{"name": "entity", "type": "person|place|concept|preference|company|skill"}}
    ]
}}

Max 5 entities. Skip if unclear."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except:
        return {"entities": []}

async def agent2_propose_relations(text: str, existing_entities: list, existing_relations: list) -> dict:
    """Check existing + propose NEW relations only"""

    existing_names = [_entity_name(e) for e in existing_entities[:10]]
    existing = "\n".join([f"- {name}" for name in existing_names if name]) or "None"
    existing_r = "\n".join([f"- {r.get('source', '')}->{r.get('relation_type', '')}->{r.get('target', '')}" for r in existing_relations[:10]]) or "None"
    
    prompt = f"""Check existing and propose NEW relations from this message.

Message: "{text}"

Existing entities: {existing}
Existing relations: {existing_r}

JSON:
{{
    "new_entities": [{{"name": "X", "type": "type"}}],
    "relations": [{{"from": "entity1", "to": "entity2", "type": "knows|lives_in|works_at|likes|uses", "why": "reason"}}]
}}

Skip if no new relations. Max 3."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=400,
            temperature=0.1
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except:
        return {"new_entities": [], "relations": []}

async def agent4_extract_context(text: str) -> dict:
    """Extract topics/intents for context graph - NOT full messages"""
    
    prompt = f"""Extract topics and intent from this message.

Message: "{text}"

JSON:
{{
    "topics": [{{"name": "topic"}}],
    "intent": "question|statement|preference|fact"
}}

Max 2 topics."""

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=200,
            temperature=0.1
        )
        content = response.choices[0].message.content
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        return json.loads(content.strip())
    except:
        return {"topics": [], "intent": "statement"}

async def chat_with_memory(user_message: str, memory_manager) -> dict:
    existing_entities = memory_manager.knowledge_graph.get_all_entities()
    existing_relations = memory_manager.knowledge_graph.get_all_relations()
    
    agent1 = await agent1_extract_entities(user_message)
    
    new_entities_added = []
    entity_name_to_id = {}
    
    for e in agent1.get("entities", []):
        name = _entity_name(e)
        if not name:
            continue
        if not any(_entity_name(ex).lower() == name.lower() for ex in existing_entities):
            try:
                result = memory_manager.knowledge_graph.add_entity(
                    name=name,
                    entity_type=e.get('type', 'concept'),
                    properties={"source_message": user_message[:100]}
                )
                if isinstance(result, dict):
                    new_entities_added.append({"name": name, "type": e.get("type", "concept")})
                    entity_name_to_id[name.lower()] = result.get('id')
            except:
                pass
    
    all_entities = memory_manager.knowledge_graph.get_all_entities()
    for e in all_entities:
        name = _entity_name(e)
        if name:
            entity_name_to_id[name.lower()] = e.get('id')
    
    agent2 = await agent2_propose_relations(user_message, all_entities, existing_relations)
    
    for e in agent2.get("new_entities", []):
        name = _entity_name(e)
        if not name:
            continue
        if not any(_entity_name(ex).lower() == name.lower() for ex in all_entities):
            try:
                result = memory_manager.knowledge_graph.add_entity(
                    name=name,
                    entity_type=e.get('type', 'concept'),
                    properties={"source_message": user_message[:100]}
                )
                if isinstance(result, dict):
                    new_entities_added.append({"name": name, "type": e.get("type", "concept")})
                    entity_name_to_id[name.lower()] = result.get('id')
            except:
                pass
    
    all_entities = memory_manager.knowledge_graph.get_all_entities()
    for e in all_entities:
        name = _entity_name(e)
        if name:
            entity_name_to_id[name.lower()] = e.get('id')
    
    relations_added = []
    for rel in agent2.get("relations", []):
        from_name = str(rel.get('from') or '').lower().strip()
        to_name = str(rel.get('to') or '').lower().strip()
        
        from_id = entity_name_to_id.get(from_name)
        to_id = entity_name_to_id.get(to_name)
        
        if not from_id:
            for e in all_entities:
                if from_name and from_name in _entity_name(e).lower():
                    from_id = e.get('id')
                    break
        if not to_id:
            for e in all_entities:
                if to_name and to_name in _entity_name(e).lower():
                    to_id = e.get('id')
                    break
        
        if from_id and to_id and from_id != to_id:
            already_exists = any(
                r.get('source') == from_id and r.get('target') == to_id
                for r in existing_relations
            )
            if not already_exists:
                try:
                    memory_manager.knowledge_graph.add_relation(
                        source_id=from_id,
                        target_id=to_id,
                        relation_type=rel.get('type', 'related_to'),
                        properties={
                            "why": rel.get('why', ''),
                            "source_message": user_message[:200]
                        },
                        confidence=0.7
                    )
                    relations_added.append(rel)
                except:
                    pass
    
    agent4 = await agent4_extract_context(user_message)
    topics = agent4.get("topics", [])
    intents = [{"intent": agent4.get("intent", "statement"), "entities": []}]
    
    all_entities_after = memory_manager.knowledge_graph.get_all_entities()
    
    for e in new_entities_added:
        e_id = entity_name_to_id.get(e['name'].lower())
        if e_id:
            memory_manager.add_entity_to_context_graph(
                e_id,
                e['name'],
                e.get('type', 'concept'),
                user_message[:100]
            )
    
    for rel in relations_added:
        from_name = str(rel.get('from') or '').lower().strip()
        to_name = str(rel.get('to') or '').lower().strip()
        
        from_id = entity_name_to_id.get(from_name)
        to_id = entity_name_to_id.get(to_name)
        
        if not from_id:
            for ent in all_entities_after:
                if from_name and from_name in _entity_name(ent).lower():
                    from_id = ent.get('id')
                    break
        if not to_id:
            for ent in all_entities_after:
                if to_name and to_name in _entity_name(ent).lower():
                    to_id = ent.get('id')
                    break
        
        if from_id and to_id and from_id != to_id:
            memory_manager.link_entities_in_context(
                from_id,
                to_id,
                f"conversational_{rel.get('type', 'related')}",
                f"mentioned in: {user_message[:150]}"
            )
    
    memory_manager.process_context_from_agent(topics, intents, [])
    memory_manager.process_input(user_message, role="user")
    
    context = memory_manager.retrieve(user_message, ["knowledge_graph"])
    kg_context = ""
    if context.get("knowledge_graph"):
        for e in context["knowledge_graph"][:3]:
            name = _entity_name(e)
            if name:
                kg_context += f"- {name} ({e.get('entity_type')})\n"
    
    system_prompt = f"You have memory: {kg_context}\nRespond naturally."
    
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            max_tokens=400
        )
        assistant_message = response.choices[0].message.content
    except:
        assistant_message = "Error occurred but message stored."

    memory_manager.process_input(assistant_message, role="assistant")
    
    return {
        "user_message": user_message,
        "assistant_message": assistant_message,
        "memory_layers_updated": ["knowledge_graph", "context_graph"],
        "entities_extracted": new_entities_added,
        "relations_extracted": relations_added,
        "topics_extracted": topics
    }
