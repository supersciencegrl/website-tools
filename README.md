# <span style="color: navy">Website tools</span>

A repo of tools for automatically interacting with <a href="https://supersciencegrl.co.uk">SuperScienceGrl.co.uk</a> &ndash; for which the source code can be found in the <a href="https://github.com/supersciencegrl/supersciencegrl.github.io">SuperScienceGrl.github.io</a> repo. 

### <span style="color: darkgreen">ScrapeConferences</span>
This user-friendly GUI tool (_ScrapeConferences.exe_) was built to read and download the contents of the <a href="https://supersciencegrl.co.uk/conferences">Conference Database</a> to a .xlsx spreadsheet for local parsing. 

### <span style="color: darkgreen">Website management scripts</span>
- _GordonConferences.py_ &ndash; Web scraper to extract html from Gordon Conference webpages to the Conference Database
- _ScientificUpdate.py_ &ndash; Web scraper to extract html from Scientific Update webpages to the Conference Database
- _link-checker.py_ &ndash; Script to check whether any links have been duplicated on a page
- _update-batch.py_ &ndash; Script to update all website html files in batch, eg: to change the website template

### <span style="color: darkgreen">Online webinar list</span>
I previously kept a list of online chemistry events (webinars, conferences, etc; list archive <a href="https://supersciencegrl.co.uk/online-old">here</a>) at the start of the Covid-19 pandemic. This turned out to be surprisingly popular, and the demand to download links directly to users' calendars required implementing automation. 

- _events_from_html.py_ &ndash; Generates both .ics downloadable calendar files (eg: Outlook) and data-rich Google Calendar events from the html code of the online webinar list, and inserts their links back into the html
- _DELETEEXTRAFILES.py_ &ndash; Removes any .ics downloadable calendar files if their time is set to the past

### <span style="color: darkgreen">Sass</span>
It's not in this repo, but another recommended automation tool for website building is <a href="https://sass-lang.com/">Sass</a>, a CSS extension language allowing seamless manipulation using 'themes'. I use Sass for <a href="https://supersciencegrl.co.uk">SuperScienceGrl.co.uk</a>. 
