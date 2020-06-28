import sqlite3

class PlexDB:
    def movie(self,db,libraryid):
        conn = sqlite3.connect(db)
        c = conn.cursor()

        c.execute("DROP TABLE IF EXISTS temp.upperDirectories")
        c.execute("create temp table upperDirectories(directoryId)")
        c.execute("""insert into upperDirectories
        select directories.id
        from directories
        where parent_directory_id is null""")
        c.execute("""select directories.path, section_locations.root_path, metadata_items.guid, metadata_item_id, metadata_items.title
        from media_parts
            join directories on directories.id = media_parts.directory_id
            join section_locations on section_locations.library_section_id = directories.library_section_id
            join media_items on media_items.id = media_parts.media_item_id
            join metadata_items on metadata_items.id = media_items.metadata_item_id
            join temp.upperDirectories on temp.upperDirectories.directoryId = directories.parent_directory_id
        where section_locations.library_section_id in (%s)
        and metadata_type in (1)""" % libraryid)

        return c.fetchall()

    def shows(self,db,libraryid):
        conn = sqlite3.connect(db)
        c = conn.cursor()

        c.execute("DROP TABLE IF EXISTS temp.topMovieSeriesDirectories")
        c.execute("create temp table topMovieSeriesDirectories(directoryId)")
        c.execute("""insert into temp.topMovieSeriesDirectories
        select directories.id
        from directories
        where parent_directory_id is null""")
        c.execute("""select *
        from temp.topMovieSeriesDirectories;""")
        c.execute("DROP TABLE IF EXISTS temp.seriesDirectories")
        c.execute("create temp table seriesDirectories(directoryId)")
        c.execute("""insert into temp.seriesDirectories
        select directories.id
        from directories
            inner join temp.topMovieSeriesDirectories on temp.topMovieSeriesDirectories.directoryId = directories.parent_directory_id and directories.parent_directory_id is not null""")
        c.execute("""select pdir.path, max(section_locations.root_path), max(metadata_items.guid), seasons.parent_id, series.title
        from media_parts
            join directories on directories.id = media_parts.directory_id
            join section_locations on section_locations.library_section_id = directories.library_section_id
            join media_items on media_items.id = media_parts.media_item_id
            join metadata_items on metadata_items.id = media_items.metadata_item_id
            join temp.seriesDirectories on temp.seriesDirectories.directoryId = directories.parent_directory_id
         left join directories pdir on pdir.id = directories.parent_directory_id
         left join metadata_items seasons on seasons.id = metadata_items.parent_id
         left join metadata_items series on series.id = seasons.parent_id
        where section_locations.library_section_id in (%s)
        and metadata_items.metadata_type in (4)
        group by directories.parent_directory_id""" % libraryid)

        return c.fetchall()