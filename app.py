import streamlit as st
import pandas as pd
from core.repositories import MilanoRepository

# Configure Streamlit page layout and title
st.set_page_config(page_title="Milano 2026 Ops Center", layout="wide")

# Initialize database repository
repo = MilanoRepository()

# Main dashboard title
st.title("Milano 2026 Incident Tracker")

# Create sidebar filter controls
st.sidebar.header("Filter Mode")
crisis_mode = st.sidebar.checkbox("CRISIS MODE ONLY", value=False)

# Load tweets based on selected filter mode
if crisis_mode:
    st.error("Displaying only High-Priority Incidents (AI Detected)")
    tweets = repo.get_incident_tweets()
else:
    tweets = repo.get_top_tweets()

# Display key metrics in three columns
col1, col2, col3 = st.columns(3)
col1.metric("Total Users", len(repo.mongo.users.distinct("user_id")))
col2.metric("Total Tweets", repo.mongo.tweets.count_documents({}))
col3.metric("Incidents Detected", repo.mongo.tweets.count_documents({"is_incident": True}))

# Display live tweet feed
st.subheader("Live Feed")
for t in tweets:
    
    # Use different avatars for normal vs incident tweets
    with st.chat_message("user" if not t.get("is_incident") else "assistant", avatar="👤" if not t.get("is_incident") else "⚠️"):
        st.markdown(f"**User:** {t['user_id']} | **Likes:** {t['favorite_count']}")
        st.markdown(t['text'])
        st.caption(f"Tags: {t['hashtags']} | Sentiment: {t.get('sentiment_score', 0):.2f}")

# Generate hashtag analytics chart
st.subheader("Top Hashtags")

# MongoDB aggregation pipeline to count hashtag usage
pipeline = [
    {"$unwind": "$hashtags"},
    {"$group": {"_id": "$hashtags", "count": {"$sum": 1}}},
    {"$sort": {"count": -1}},
    {"$limit": 10}
]
tags_data = list(repo.mongo.tweets.aggregate(pipeline))

# Display bar chart if data exists
if tags_data:
    df_tags = pd.DataFrame(tags_data)
    st.bar_chart(df_tags.set_index("_id"))