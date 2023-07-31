# thaimanga_scraping
Fetch data and images of Manga, Manhua and Manhwa from Thaimanga.net

This script made for scraping data and image for Manga, Manhua and Manhwa from Thaimanga.net.

# Function work :
- Fetch all manga, manghwa and manhua from Thaimanga.net and save in seperate folder by using category and title as foldername ex. [{category}] {title}.
- Fetch chapter in each manga, manghwa and manhua from Thaimanga.net and save them in seperate folder.
- save data of manga, manghwa and manhua to data\{manga}.txt for better work when run this script in next time ex. data\{manga_data}.txt.
- Can fetch chapter continue from last running. (when you want to update them.)
- Skip files and chapter links have been visited.
- Support multi-thread fetching manga (limit to 16 thhreads).
- Save failed image download chapter to failed folder.
- Can check size between local and remote. If not same, try to new download.
- Check number of files in chapter folder.
