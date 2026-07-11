import sys
import os
import json

sys.path.append(os.getcwd())
from semantic_engine.main import SemanticEngine

text = "দৃশ্য ১ ঢাকা। এই প্ল্যানেটের অন্যতম ক্রাউডেড একটা মেগাসিটি। দৃশ্য ২ দুই কোটিরও বেশি মানুষ এখানে বাঁচছে, লড়ছে আর প্রতিনিয়ত কংক্রিটের পাহাড় বানাচ্ছে। দৃশ্য ৩ কিন্তু মানুষের তৈরি এই বিশাল সাম্রাজ্যের নিচেই লুকিয়ে আছে একটা টাইমবোম্ব। দৃশ্য ৪ একটা জিওলজিক্যাল ক্লক, যার টিকটিক শব্দ সময়ের সাথে সাথে আরও তীব্র হচ্ছে"

engine = SemanticEngine()
result = engine.process(text)
print(json.dumps(result, indent=2, ensure_ascii=False))
