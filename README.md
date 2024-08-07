# Elevate
-this python script uses the spotify api to evolve and enchance the anghami search engine by using its data to match the anghami data base becoming more accurate,personalized,less static and stale. making it more appealing to the user and develops a constant relief and trust that the user will consume (as in music) what ever they desire appealing to thier sense of control.

-as to its main functions: As a demo given to us by our coordinator he gave us a list of keywords(input.txt) which promts the api to search its entire data base with these key words and then gives us (output.txt) with its term,rank,name,isrc,upc,id(for an artist,track or album),popularity,release date,genre,followers all depending in what the database has to offer.

# search.py examples:
  -input.txt: future
    -csv output:
      track.csv:
        #term // ranks // name // ISRC // ID // artist // album // release_date // popularity
        future,1,Throw Away,USSM11913507,2ML7vSeIZEmOCOiLUmz7Sv,Future,Monster,2014-10-28,67
        future,2,Like That,USSM12402041,2tudvzsrR56uom6smgOcSf,"Future, Metro Boomin, Kendrick Lamar",WE DON'T TRUST YOU,2024-03-22,89
        future,3,Low Life (feat. The Weeknd),USSM11600557,7EiZI6JVHllARrX9PUvAdX,"Future, The Weeknd",EVOL,2016-04-13,77
        future,4,Type Shit,USSM12402033,28drn6tQo95MRvO0jQEo5C,"Future, Metro Boomin, Travis Scott, Playboi Carti",WE DON'T TRUST YOU,2024-03-22,87
        future,5,Solo,USSM11701733,4lH6nENd1y81jp7Yt9lTBX,Future,HNDRXX,2017-07-27,80
  
      album.csv:
        #term // ranks // name // upc // id // artist // Total_Tracks
        future,1,WE DON'T TRUST YOU,196871937382,4iqbFIdGOTzXeDtt9owjQn,"Future, Metro Boomin",17
        future,2,Future Nostalgia,190295252960,7fJJK56U9fHixgO0HQkhtI,Dua Lipa,11
        future,3,DS2 (Deluxe),886445398274,0fUy6IdLHDpGNwavIlhEsl,Future,19
        future,4,FUTURE,886446597102,17FBoXK1NU2rvJBbzdzw0r,Future,20
        future,5,WE STILL DON'T TRUST YOU,196871990844,3bSNhnaQQXpC639OQ4pMyP,"Future, Metro Boomin",25
  
      artist.csv:
        #term // ranks // name // id // genres // followers // popularity
        future,1,Future,1RyvyyTE3xzB2ZywiAwp0i,"atl hip hop, hip hop, rap, southern hip hop, trap",17861614,91
        future,2,Future Islands,1WvvwcQx0tj6NdDhZZ2zZz,"alternative dance, art pop, baltimore indie, chamber pop, indie rock, indietronica, neo-synthpop, shimmerpop",615220,60
        future,3,Metro Boomin,0iEtIxbK0KxaSlF7G42ZOp,rap,8809110,89
        future,4,Futurebirds,4Ait1vX2ZaWPrkua8Z664O,athens indie,58673,45
        future,5,Drake,3TVXtAsR1Inumwj472S9r4,"canadian hip hop, canadian pop, hip hop, pop rap, rap",90089346,94

    -DB output:
        mysql> select * from artist;
        +--------+-------+----------------+------------------------+---------------------------------------------------------------------------------------------------------------+-----------+------------+
        | term   | ranks | name           | id                     | genres                                                                                                        | followers | popularity |
        +--------+-------+----------------+------------------------+---------------------------------------------------------------------------------------------------------------+-----------+------------+
        | future |     1 | Future         | 1RyvyyTE3xzB2ZywiAwp0i | atl hip hop, hip hop, rap, southern hip hop, trap                                                             |  17861614 |         91 |
        | future |     2 | Future Islands | 1WvvwcQx0tj6NdDhZZ2zZz | alternative dance, art pop, baltimore indie, chamber pop, indie rock, indietronica, neo-synthpop, shimmer pop |    615220 |         60 |
        | future |     3 | Metro Boomin   | 0iEtIxbK0KxaSlF7G42ZOp | rap                                                                                                           |   8809110 |         89 |
        | future |     4 | Futurebirds    | 4Ait1vX2ZaWPrkua8Z664O | athens indie                                                                                                  |     58673 |         45 |
        | future |     5 | Drake          | 3TVXtAsR1Inumwj472S9r4 | canadian hip hop, canadian pop, hip hop, pop rap, rap                                                         |  90089346 |         94 |
        +--------+-------+----------------+------------------------+---------------------------------------------------------------------------------------------------------------+-----------+------------+
        5 rows in set (0.00 sec)
        
        mysql> select * from track;
        +--------+-------+-----------------------------+--------------+------------------------+---------------------------------------------------+--------------------+--------------+------------+
        | term   | ranks | name                        | isrc         | id                     | artist                                            | album              | release_date | popularity |
        +--------+-------+-----------------------------+--------------+------------------------+---------------------------------------------------+--------------------+--------------+------------+
        | future |     1 | Throw Away                  | USSM11913507 | 2ML7vSeIZEmOCOiLUmz7Sv | Future                                            | Monster            | 2014-10-28   |         67 |
        | future |     2 | Like That                   | USSM12402041 | 2tudvzsrR56uom6smgOcSf | Future, Metro Boomin, Kendrick Lamar              | WE DON'T TRUST YOU | 2024-03-22   |         89 |
        | future |     3 | Low Life (feat. The Weeknd) | USSM11600557 | 7EiZI6JVHllARrX9PUvAdX | Future, The Weeknd                                | EVOL               | 2016-04-13   |         77 |
        | future |     4 | Type Shit                   | USSM12402033 | 28drn6tQo95MRvO0jQEo5C | Future, Metro Boomin, Travis Scott, Playboi Carti | WE DON'T TRUST YOU | 2024-03-22   |         87 |
        | future |     5 | Solo                        | USSM11701733 | 4lH6nENd1y81jp7Yt9lTBX | Future                                            | HNDRXX             | 2017-07-27   |         80 |
        +--------+-------+-----------------------------+--------------+------------------------+---------------------------------------------------+--------------------+--------------+------------+
        5 rows in set (0.00 sec)
        
        mysql> select * from album;
        +--------+-------+--------------------------+--------------+------------------------+----------------------+--------------+
        | term   | ranks | name                     | upc          | id                     | artist               | Total_Tracks |
        +--------+-------+--------------------------+--------------+------------------------+----------------------+--------------+
        | future |     1 | WE DON'T TRUST YOU       | 196871937382 | 4iqbFIdGOTzXeDtt9owjQn | Future, Metro Boomin |           17 |
        | future |     2 | Future Nostalgia         | 190295252960 | 7fJJK56U9fHixgO0HQkhtI | Dua Lipa             |           11 |
        | future |     3 | DS2 (Deluxe)             | 886445398274 | 0fUy6IdLHDpGNwavIlhEsl | Future               |           19 |
        | future |     4 | FUTURE                   | 886446597102 | 17FBoXK1NU2rvJBbzdzw0r | Future               |           20 |
        | future |     5 | WE STILL DON'T TRUST YOU | 196871990844 | 3bSNhnaQQXpC639OQ4pMyP | Future, Metro Boomin |           25 |
        +--------+-------+--------------------------+--------------+------------------------+----------------------+--------------+
        5 rows in set (0.00 sec)

# similars.py example:
  artist_input.txt:Ryan Jon

  spot database output: 
      +------------------+------------------------+-------+--------------------------+------------------------+
      | artist           | artist_id              | ranks | similar_a                | sim_ID                 |
      +------------------+------------------------+-------+--------------------------+------------------------+
      | Ryan Jon         | 31z9f9AyPawiq0qlBO1M3i |     1 | Hayes Carll              | 6UWifcscEdbjPgmbevBxZV |
      | Ryan Jon         | 31z9f9AyPawiq0qlBO1M3i |     2 | Turnpike Troubadours     | 1YSA4byX5AL1zoTsSTlB03 |
      | Ryan Jon         | 31z9f9AyPawiq0qlBO1M3i |     3 | Chris Knight             | 2XJzOLYV2mF5K2JfUhJEK0 |
      | Ryan Jon         | 31z9f9AyPawiq0qlBO1M3i |     4 | Reckless Kelly           | 0jmPjksXqVrO92Urmx58vg |
      | Ryan Jon         | 31z9f9AyPawiq0qlBO1M3i |     5 | Shane Smith & the Saints | 4pLxUMyDrijXynrUP59whJ |
      +------------------+------------------------+-------+--------------------------+------------------------+


![spot-chart2](https://github.com/user-attachments/assets/c574648c-1e0b-4e21-8ebf-9fca0b858342)
![spot-chart](https://github.com/user-attachments/assets/ff2ab0a9-b52e-4048-8f6e-f7f70b676b1a)
