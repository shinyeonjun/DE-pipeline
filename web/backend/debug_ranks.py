import asyncio
import sys
import os
from collections import Counter

# Add backend directory to path so we can import app modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.core.database import supabase

async def check_anomalies():
    print("=== 1. Checking Video Ranks ===")
    
    # Get latest snapshot time
    time_result = supabase.table('fact_video_snapshots')\
        .select('snapshot_at')\
        .order('snapshot_at', desc=True)\
        .limit(1)\
        .execute()
        
    if not time_result.data:
        print("No data found in fact_video_snapshots")
        return

    latest_time = time_result.data[0]['snapshot_at']
    print(f"Latest Snapshot: {latest_time}")

    # deep dive into Rank 1
    print("\n--- Videos with Rank 1 ---")
    rank1_videos = supabase.table('fact_video_snapshots')\
        .select('video_id, title, view_count, channel_name')\
        .eq('snapshot_at', latest_time)\
        .eq('trending_rank', 1)\
        .execute()
        
    for v in rank1_videos.data:
        print(f"ID: {v['video_id']} | Title: {v['title'][:40]}... | Ch: {v['channel_name']}")

    print("\n=== 2. Checking Other Tables ===")
    
    # Check Comments
    print("\n--- Fact Comments Sample (Latest) ---")
    comments = supabase.table('fact_comments')\
        .select('comment_id, collected_at')\
        .order('collected_at', desc=True)\
        .limit(10)\
        .execute()
        
    # Check for duplicate comment_ids in recent batch
    if comments.data:
        last_time = comments.data[0]['collected_at']
        print(f"Latest Comment Time: {last_time}")
        recent_comments = supabase.table('fact_comments')\
            .select('comment_id')\
            .eq('collected_at', last_time)\
            .execute()
            
        c_ids = [c['comment_id'] for c in recent_comments.data]
        dups = [item for item, count in Counter(c_ids).items() if count > 1]
        print(f"Total Comments in batch: {len(c_ids)}")
        print(f"Duplicate Comment IDs found: {len(dups)}")
    else:
        print("No comments found.")

    # Check Channels
    print("\n--- Fact Channels Sample (Latest) ---")
    channels = supabase.table('fact_channel_stats')\
        .select('channel_id, collected_at')\
        .order('collected_at', desc=True)\
        .limit(1)\
        .execute()
        
    if channels.data:
        last_ch_time = channels.data[0]['collected_at']
        print(f"Latest Channel Time: {last_ch_time}")
        recent_channels = supabase.table('fact_channel_stats')\
            .select('channel_id')\
            .eq('collected_at', last_ch_time)\
            .execute()
            
        ch_ids = [c['channel_id'] for c in recent_channels.data]
        ch_dups = [item for item, count in Counter(ch_ids).items() if count > 1]
        print(f"Total Channels in batch: {len(ch_ids)}")
        print(f"Duplicate Channel IDs found: {len(ch_dups)}")
    else:
        print("No channels found.")

if __name__ == "__main__":
    asyncio.run(check_anomalies())
