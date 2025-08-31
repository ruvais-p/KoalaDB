"""
KoalaDB Test Script
-------------------
This script demonstrates all major functionalities of KoalaDB with step-by-step
examples for Students and Teachers collections. It covers:
 - Initialization and collection creation
 - Document creation (with/without custom IDs)
 - Adding & updating data
 - Media file storage and retrieval
 - Querying (find, find_one, queries with operators)
 - Date/time based queries
 - Updating and deleting (with media cleanup)
 - Grouping, counting, and statistics
 - Using helper functions like touch() and cleanup
"""

from koaladb import KoalaDB, DateTimeHelpers, Document
from datetime import datetime, timedelta
import time, os, shutil
from pathlib import Path

# -------------------------------------------------------------------------
# Helper: Create sample image files (simulating profile pictures, certificates etc.)
# -------------------------------------------------------------------------
def create_sample_images():
    sample_dir = Path("sample_images")
    sample_dir.mkdir(exist_ok=True)

    image_files = {
        "alice.jpg": "Alice profile image",
        "bob.png": "Bob profile image",
        "charlie.gif": "Charlie profile image",
        "diana.webp": "Diana profile image",
        "teacher1.jpg": "Teacher 1 profile image",
        "teacher2.png": "Teacher 2 profile image",
    }
    for filename, content in image_files.items():
        with open(sample_dir / filename, "w") as f:
            f.write(content)
    return sample_dir


# -------------------------------------------------------------------------
# MAIN DEMO STARTS HERE
# -------------------------------------------------------------------------
if __name__ == "__main__":
    # 1. Setup
    sample_dir = create_sample_images()
    KoalaDB.initialize()
    KoalaDB.createCollection("Student")
    KoalaDB.createCollection("Teacher")

    students_db = KoalaDB.collection("Student")
    teachers_db = KoalaDB.collection("Teacher")

    # ---------------------------------------------------------------------
    # 2. Create Students with media
    # ---------------------------------------------------------------------
    print("\n=== STUDENT DOCUMENT CREATION ===")
    alice = students_db.create().add({
        "name": "Alice", "age": 21, "grade": "A",
        "email": "alice@school.edu", "courses": ["Math", "Physics", "CS"]
    })
    alice.add_media_file(str(sample_dir / "alice.jpg"), "profile_image")

    time.sleep(1)  # spacing timestamps

    bob = students_db.create("student_bob_123").add({
        "name": "Bob", "age": 22, "grade": "B",
        "email": "bob@school.edu", "courses": ["Biology", "Chemistry", "English"]
    })
    bob.add_media_file(str(sample_dir / "bob.png"), "profile_image")

    time.sleep(1)

    charlie = students_db.create().add({
        "name": "Charlie", "age": 20, "grade": "A",
        "email": "charlie@school.edu", "courses": ["Art", "History", "Music"]
    })
    charlie.add_media_file(str(sample_dir / "charlie.gif"), "profile_image")

    diana = students_db.create().add({
        "name": "Diana", "age": 23, "grade": "C",
        "email": "diana@school.edu", "courses": ["Economics", "Business"]
    })
    diana.add_media_file(str(sample_dir / "diana.webp"), "profile_image")
    diana.add_multiple_media_files(
        [str(sample_dir / "alice.jpg"), str(sample_dir / "bob.png")],
        "additional_photos"
    )

    # ---------------------------------------------------------------------
    # 3. Create Teachers with media
    # ---------------------------------------------------------------------
    print("\n=== TEACHER DOCUMENT CREATION ===")
    teacher1 = teachers_db.create().add({
        "name": "Dr. Smith", "subject": "Mathematics",
        "email": "smith@school.edu", "office_hours": ["Mon 2-4pm"], "experience_years": 15
    })
    teacher1.add_media_file(str(sample_dir / "teacher1.jpg"), "profile_image")

    teacher2 = teachers_db.create().add({
        "name": "Prof. Johnson", "subject": "Physics",
        "email": "johnson@school.edu", "office_hours": ["Tue 1-3pm"], "experience_years": 8
    })
    teacher2.add_media_file(str(sample_dir / "teacher2.png"), "profile_image")

    # ---------------------------------------------------------------------
    # 4. Find, Count and Display
    # ---------------------------------------------------------------------
    print("\n=== FIND & COUNT OPERATIONS ===")
    print("All students:", students_db.count())
    print("All teachers:", teachers_db.count())
    print("First student found:", students_db.find_one())
    print("Math teachers:", teachers_db.find(query={"subject": "Mathematics"}))

    # ---------------------------------------------------------------------
    # 5. Update operations
    # ---------------------------------------------------------------------
    print("\n=== UPDATE OPERATIONS ===")
    students_db.update("student_bob_123", {"grade": "A-", "honors": True})
    students_db.store_media_file(str(sample_dir / "charlie.gif"), "student_bob_123", "certificate")

    # Demonstrate touch()
    bob_doc = Document(students_db, "student_bob_123")
    bob_doc.touch()
    print("Bob after update:", students_db.find("student_bob_123"))

    # ---------------------------------------------------------------------
    # 6. Date/Time Operations
    # ---------------------------------------------------------------------
    print("\n=== DATE/TIME QUERIES ===")
    now = datetime.now()
    yesterday = now - timedelta(days=1)

    print("Created between yesterday and now:", students_db.find_created_between(yesterday, now))
    print("Recent (<48h):", students_db.find_recent(hours=48))
    print("Older than 0 days:", students_db.find_older_than(days=0))

    for sid, sdata in students_db.find().items():
        doc = Document(students_db, sid)
        print(f"{sdata['name']} age(days): {doc.get_age_in_days():.3f}")

    grouped = students_db.group_by_date()
    print("Grouped by date:", grouped.keys())

    # ---------------------------------------------------------------------
    # 7. Document Media Retrieval
    # ---------------------------------------------------------------------
    print("\n=== MEDIA RETRIEVAL ===")
    alice_doc = Document(students_db, alice.object_id)
    print("Alice image path:", alice_doc.get_media_file_path("profile_image"))
    print("Alice image URL:", alice_doc.get_media_file_url("profile_image"))

    # ---------------------------------------------------------------------
    # 8. Cleanup Operations
    # ---------------------------------------------------------------------
    print("\n=== CLEANUP ===")
    print("Cleanup old docs (>0 days):", students_db.cleanup_old_documents(days=0))

    # Delete one teacher
    teachers_db.delete_many({"experience_years": {"$lt": 10}})
    print("Remaining teachers:", teachers_db.count())

    # ---------------------------------------------------------------------
    # 9. Date Helpers
    # ---------------------------------------------------------------------
    print("\n=== DATE HELPERS ===")
    print("Start of day:", DateTimeHelpers.get_start_of_day())
    print("Start of week:", DateTimeHelpers.get_start_of_week())
    print("Start of month:", DateTimeHelpers.get_start_of_month())

    # ---------------------------------------------------------------------
    # 10. Final Database Info
    # ---------------------------------------------------------------------
    print("\n=== FINAL INFO ===")
    print("Database location:", os.path.abspath(KoalaDB.db_path))
    print("Media store files:", list(Path(KoalaDB.store_path).glob('*')))

    # Cleanup sample image directory
    shutil.rmtree(sample_dir)
    print("Cleaned up sample images dir")
    print("\n=== TEST COMPLETED SUCCESSFULLY ===")
