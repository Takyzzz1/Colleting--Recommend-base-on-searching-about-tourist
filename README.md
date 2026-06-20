# Technical Design Specification

# Multi-Agent AI Travel Planning System

Version: 2.0

---

# 1. Introduction

## 1.1 Purpose

The purpose of this project is to develop an intelligent Multi-Agent AI Travel Planning System capable of assisting users throughout the complete travel planning process.

The system is designed around the concept of Agentic AI, where multiple specialized AI agents collaborate to solve complex travel planning tasks rather than relying on a single monolithic prompt.

The application should generate an optimized travel plan based on user preferences, budget, interests, weather conditions, and real-time travel information.

---

# 1.2 Design Principles

The system follows these principles:

• Single Responsibility per Agent

Each agent should have only one responsibility.

• Tool-based Architecture

Agents should use tools rather than embedding business logic.

• Hybrid Knowledge Retrieval

Static knowledge → RAG

Dynamic knowledge → Tavily

Realtime information → External APIs

• Shared State

All agents communicate only through LangGraph State.

Agents must never communicate directly.

---

# 2. High-Level Architecture

                    User
                      │
                      ▼
             Supervisor Agent
                      │
      ┌───────────────┴───────────────┐
      ▼                               ▼
 General Agent            Travel Planning Workflow
                                      │
                                      ▼
                       Travel Knowledge Agent
                         │            │
                  RAG Tool      Tavily Tool
                                      │
                                      ▼
                             Planner Agent
                         ┌──────┼────────┐
                         ▼      ▼        ▼
                  Weather   Maps   Budget Tool
                         │
                         ▼
                 Final Travel Plan

---

# 3. Agent Responsibilities

The system consists of four logical agents.

1. Supervisor Agent

2. General Agent

3. Travel Knowledge Agent

4. Planner Agent

No additional agents should be created unless necessary.

Business logic should remain inside Tools whenever possible.

---

# 4. Supervisor Agent

## Responsibility

The Supervisor Agent is the entry point of the application.

Responsibilities

• Understand user intent

• Decide execution workflow

• Route requests

• Maintain LangGraph State

• Invoke specialized agents

The Supervisor never performs reasoning about travel.

It only orchestrates.

Example

User

"I want a 4-day trip to Da Nang under 12 million."

Execution

Supervisor

↓

Travel Knowledge Agent

↓

Planner Agent

↓

Return response

---

# 5. General Agent

Purpose

Handle conversations unrelated to travel planning.

Examples

Greetings

General Questions

Travel Tips

Visa Questions

Packing Advice

The General Agent does not use:

RAG

Tavily

Weather API

Maps API

Budget Tool

---

# 6. Travel Knowledge Agent

Purpose

Provide travel knowledge.

Responsibilities

Retrieve destination information.

Merge knowledge from multiple sources.

Never generate travel plans.

Never estimate budgets.

Never generate itineraries.

Instead, provide structured travel context.

---

Knowledge Sources

Static Knowledge

Provided by RAG.

Contains

History

Culture

Cuisine

Travel Etiquette

Transportation Guide

Destination Overview

Travel Tips

Dynamic Knowledge

Provided by Tavily.

Contains

Hotel Prices

Tour Prices

Airline Tickets

Tourist News

Restaurant Reviews

Festivals

Trending Destinations

Events

The Travel Knowledge Agent should automatically decide whether

RAG

Tavily

or both

are required.

---

Output Example

Destination Summary

Recommended Attractions

Local Food

Transportation

Hotel Information

Flight Information

Tour Prices

Travel News

Festival Information

---

# 7. Planner Agent

The Planner Agent is the intelligence center of the application.

It receives

Travel Context

User Preferences

Budget

Weather

Travel Dates

Interests

Then generates

Personalized Travel Plan

The Planner Agent should never search information itself.

Instead it must use Tools.

---

Planner Tools

Weather Tool

Google Maps Tool

Budget Calculator

Preference Optimizer

Schedule Generator

---

Planner Workflow

Need weather?

↓

Weather Tool

Need travel distance?

↓

Maps Tool

Need cost estimation?

↓

Budget Tool

Generate itinerary

Return response

---

Planner Output

Daily itinerary

Estimated budget

Recommended hotels

Recommended restaurants

Transportation

Warnings

Travel tips

---

# 8. Tool Specification

## 8.1 RAG Tool

Purpose

Retrieve static travel knowledge.

Vector Store

ChromaDB

Embedding

HuggingFace

Knowledge

History

Culture

Cuisine

Travel Guide

Destination Overview

---

## 8.2 Tavily Tool

Purpose

Retrieve realtime information.

Typical Queries

Tour Prices

Flight Prices

Hotel Prices

Restaurant Reviews

Tourist News

Events

Travel Warnings

Festivals

Trending Places

All Tavily results must be summarized before entering the graph state.

---

## 8.3 Weather Tool

Purpose

Retrieve weather forecast.

Output

Temperature

Rain

Humidity

Weather Condition

Planner decides how to use it.

---

## 8.4 Maps Tool

Purpose

Estimate

Travel Distance

Travel Duration

Route

Planner decides how to optimize itinerary.

---

## 8.5 Budget Tool

Purpose

Estimate travel expenses.

Inputs

Hotel

Transportation

Flights

Food

Activities

Shopping

Output

Budget Breakdown

Remaining Budget

Budget Suggestions

The Budget Tool must not perform reasoning.

Only calculation.

---

# 9. RAG Knowledge Base

The RAG database intentionally remains lightweight.

The objective is not replacing Tavily.

Instead it provides reliable background knowledge.

Folder Structure

data/

    destinations/

    culture/

    cuisine/

    travel_guides/

    travel_tips/

Example Documents

Da Nang

Hoi An

Hue

Da Lat

Phu Quoc

Sa Pa

Nha Trang

Estimated Size

20–30 destinations

Each document

2–5 pages

Total

100–200 pages

---

# 10. LangGraph State

Every node shares the same state.

Example

class TravelState(TypedDict):

    messages

    user_query

    destination

    travel_dates

    duration

    budget

    interests

    rag_context

    tavily_context

    weather

    travel_distance

    estimated_budget

    itinerary

    final_response

No agent should maintain private memory.

---

# 11. Project Structure

travel-agent/

    app/

        graph.py

        state.py

        supervisor.py

        router.py

    agents/

        general_agent.py

        travel_knowledge_agent.py

        planner_agent.py

    tools/

        rag.py

        tavily.py

        weather.py

        maps.py

        budget.py

    prompts/

        supervisor.md

        general.md

        travel_knowledge.md

        planner.md

    data/

        destinations/

        culture/

        cuisine/

        travel_guides/

    vector_db/

    ui/

        gradio.py

    tests/

    README.md

---

# 12. Development Rules

Every Agent

• Only one responsibility

Every Tool

• No reasoning

Only data retrieval or calculation

Planner

• Only planner

Never search

Travel Knowledge Agent

• Only retrieve information

Never generate itinerary

Supervisor

• Only orchestration

Never answer user directly

---

# 13. Future Extensions

Google Places API

Booking API

Amadeus Flight API

Calendar Integration

Expense Tracker

Voice Assistant

Travel Memory

Multi-language Support

PDF Export

Mobile Application
