import streamlit as st
import pandas as pd
from core.repositories import MilanoRepository

st.set_page_config(page_title="Milano 2026 Ops Center", layout="wide")

repo = MilanoRepository()

st.title("Milano 2026 Incident Tracker")

# Sidebar Filters
st.sidebar.header("Filter Mode")
crisis_mode = st.sidebar.checkbox("CRISIS MODE ONLY", value=False)

# Fetch Data
if crisis_mode:
    st.error("Displaying only High-Priority Incidents (AI Detected)")
    tweets = repo.get_incident_tweets()
else:
    tweets = repo.get_top_tweets()

# Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Users", len(repo.mongo.users.distinct("user_id")))
col2.metric("Total Tweets", repo.mongo.tweets.count_documents({}))
col3.metric("Incidents Detected", repo.mongo.tweets.count_documents({"is_incident": True}))

# Main Feed
st.subheader("Live Feed")
for t in tweets:
    with st.chat_message("user" if not t.get("is_incident") else "assistant", avatar="👤" if not t.get("is_incident") else "⚠️"):
        st.markdown(f"**User:** {t['user_id']} | **Likes:** {t['favorite_count']}")
        st.markdown(t['text'])
        st.caption(f"Tags: {t['hashtags']} | Sentiment: {t.get('sentiment_score', 0):.2f}")

# Charts
st.subheader("Top Hashtags")
pipeline = [
    {"$unwind": "$hashtags"},
    {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
tags_data = list(repo.mongo.tweets.aggregate(pipeline))
if tags_data:
    df_tags = pd.DataFrame(tags_data)
    st.bar_chart(df_tags.set_index("_id"))