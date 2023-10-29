#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
db = db_setup(app)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  # Show Recent Listed Artists
  recent_artists = Artist.query.order_by(Artist.id.desc()).limit(10).all()
  # Show Recent Listed Venues
  recent_venues = Venue.query.order_by(Venue.id.desc()).limit(10).all()
  return render_template('pages/home.html', artists=recent_artists, venues=recent_venues)

#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  # get all venues grouping by id, city and state
  venues = Venue.query.group_by(Venue.id, Venue.city, Venue.state).all()
  data = []
  state_city = ''
  for venue in venues:
      # get the current state and city
      current_state_city = venue.state + venue.city
      # get all venues by city and state
      venue_data = Venue.query.filter_by(city=venue.city, state=venue.state).all()
      # add unique venues to the data
      if state_city != current_state_city:
        data.append({
          'city': venue.city,
          'state': venue.state,
          'venues': []
        })
      # get the number of upcoming shows for the current venue
        current_time = datetime.now()
        num_upcoming_shows = Show.query.filter(
            Show.venue_id == venue.id, Show.start_time > current_time).count()
        # add the current venue to the last object in data
        data[len(data) - 1]["venues"].append({
            "id": venue.id,
            "name": venue.name,
            "num_upcoming_shows": num_upcoming_shows
        })

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  # get the search term
  search_term = request.form.get('search_term', '')
  # get the results for the search term including cities and states
  results = Venue.query.filter(Venue.name.ilike(f'%{search_term}%') | Venue.city.ilike(f'%{search_term}%') | Venue.state.ilike(f'%{search_term}%')).all()
  # get the number of results
  results_count = len(results)
  # get the current time
  current_time = datetime.now()
  # get the data
  data = []
  for result in results:
      # add the current venue to the data
      data.append({
          "id": result.id,
          "name": result.name
      })
  # return the response
  response = {
      "count": results_count,
      "data": data
  }
  
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  # get the venue by id
  venue = Venue.query.get(venue_id)
  # get the current time
  current_time = datetime.now()
  upcoming_shows = []
  past_shows = []
  # get the past shows
  past_shows_list = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id, Show.start_time < current_time).all()
  
  # append the past shows to the data if there are any
  for show in past_shows_list:
    past_shows.append({
      "artist_id": show.artist_id,
      "artist_name": show.Artist.name,
      "artist_image_link": show.Artist.image_link,
      "start_time": str(show.start_time)
    })

  # get the upcoming shows
  upcoming_shows_list = db.session.query(Show).join(Artist).filter(Show.venue_id == venue_id, Show.start_time > current_time).all()
  # append the upcoming shows to the data
  for show in upcoming_shows_list:
    upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.Artist.name,
        "artist_image_link": show.Artist.image_link,
        "start_time": str(show.start_time)
    })

  # get the past shows count
  past_shows_count = len(past_shows)
  # get the upcoming shows count
  upcoming_shows_count = len(upcoming_shows)

  # get the data
  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": past_shows_count,
      "upcoming_shows_count": upcoming_shows_count,
  }

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion
  error = False
  # use try except to catch any errors
  try:
    # create a new venue object
    venue = Venue(
        name=request.form['name'],
        city=request.form['city'],
        state=request.form['state'],
        address=request.form['address'],
        phone=request.form['phone'],
        facebook_link=request.form['facebook_link'],
        image_link=request.form['image_link'],
        website=request.form['website_link'],
        genres=request.form.getlist('genres'),
        seeking_talent=True if 'seeking_talent' in request.form else False,
        seeking_description=request.form['seeking_description']
    )
    # insert the new venue object into the database
    db.session.add(venue)
    db.session.commit()
  except:
    error = True
    # rollback the session
    db.session.rollback()
  finally:
    # close the session
    db.session.close()

  if error:
    # TODO: on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Venue ' +
          request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  # delete the venue using try except to catch any errors
  
  error = False
  try:
    venue = Venue.query.get(venue_id)
    # delete all shows for the venue
    Show.query.filter_by(venue_id=venue_id).delete()
    db.session.delete(venue)
    db.session.commit()
  except:
    error = True
    db.session.rollback()
  finally:
    db.session.close()
  if error: 
    flash('Venue {venue_id} was not deleted.')
  if not error: 
    flash('Venue {venue_id} was successfully deleted.')
  return render_template('pages/home.html')

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  # query all artists in the database
  data = Artist.query.all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # search for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  # get the search term
  search_term = request.form.get('search_term', '')
  # get the results for the search term by name
  results = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  # get the number of results
  results_count = len(results)
  # get the data
  data = []
  for result in results:
      # add the current venue to the data
      data.append({
          "id": result.id,
          "name": result.name
      })
  # return the response
  response = {
      "count": results_count,
      "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: replace with real artist data from the artist table, using artist_id
  
  # get the artist by id
  artist = Artist.query.get(artist_id)
  # get the current time
  current_time = datetime.now()
  upcoming_shows = []
  past_shows = []
  # get the past shows
  past_shows_list = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id, Show.start_time < current_time).all()
  # append the past shows to the data if there are any
  for show in past_shows_list:
    past_shows.append({
      "venue_id": show.venue_id,
      "venue_name": show.Venue.name,
      "venue_image_link": show.Venue.image_link,
      "start_time": str(show.start_time)
    })
  # get the upcoming shows
  upcoming_shows_list = db.session.query(Show).join(Venue).filter(Show.artist_id == artist_id, Show.start_time > current_time).all()
  # append the upcoming shows to the data
  for show in upcoming_shows_list:
    upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.Venue.name,
        "venue_image_link": show.Venue.image_link,
        "start_time": str(show.start_time)
    })
  # get the past shows count
  past_shows_count = len(past_shows)
  # get the upcoming shows count
  upcoming_shows_count = len(upcoming_shows)
  # get the data
  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": past_shows_count,
      "upcoming_shows_count": upcoming_shows_count,
  }

  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  form = ArtistForm(request.form)
  artist_data = Artist.query.get(artist_id)
  if artist_data:
    artist = Artist.details(artist_data)
    form.name.data = artist["name"]
    form.genres.data = artist["genres"]
    form.city.data = artist["city"]
    form.state.data = artist["state"]
    form.phone.data = artist["phone"]
    form.website_link.data = artist["website"]
    form.facebook_link.data = artist["facebook_link"]
    form.seeking_venue.data = artist["seeking_venue"]
    form.seeking_description.data = artist["seeking_description"]
    form.image_link.data = artist["image_link"]
    return render_template('forms/edit_artist.html', form=form, artist=artist)
  return render_template('errors/404.html'), 404

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes

  form = ArtistForm(request.form)
  artist_data = Artist.query.get(artist_id)
  if artist_data:
    if form.validate():
      seeking_venue = False
      seeking_description = ''
      if 'seeking_venue' in request.form:
          seeking_venue = request.form['seeking_venue'] == 'y'
      if 'seeking_description' in request.form:
          seeking_description = request.form['seeking_description']
      setattr(artist_data, 'name', request.form['name'])
      setattr(artist_data, 'genres', request.form.getlist('genres'))
      setattr(artist_data, 'city', request.form['city'])
      setattr(artist_data, 'state', request.form['state'])
      setattr(artist_data, 'phone', request.form['phone'])
      setattr(artist_data, 'website', request.form['website_link'])
      setattr(artist_data, 'facebook_link', request.form['facebook_link'])
      setattr(artist_data, 'image_link', request.form['image_link'])
      setattr(artist_data, 'seeking_description', seeking_description)
      setattr(artist_data, 'seeking_venue', seeking_venue)

      # update the artist using try except to catch any errors
      try:
        db.session.commit()
        # on successful db update, flash success
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
      except:
        # rollback the session
        db.session.rollback()
      finally:
        # close the session
        db.session.close()
      return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        print(form.errors)
  return render_template('errors/404.html'), 404

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  form = VenueForm()
  venue_query = Venue.query.get(venue_id)
  # TODO: populate form with values from venue with ID <venue_id>
  if venue_query:
    venue_details = Venue.detail(venue_query)
    form.name.data = venue_details["name"]
    form.genres.data = venue_details["genres"]
    form.address.data = venue_details["address"]
    form.city.data = venue_details["city"]
    form.state.data = venue_details["state"]
    form.phone.data = venue_details["phone"]
    form.website_link.data = venue_details["website"]
    form.facebook_link.data = venue_details["facebook_link"]
    form.seeking_talent.data = venue_details["seeking_talent"]
    form.seeking_description.data = venue_details["seeking_description"]
    form.image_link.data = venue_details["image_link"]
    return render_template('forms/edit_venue.html', form=form, venue=venue_details)
  return render_template('errors/404.html'), 404

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: take values from the form submitted, and update existing
  form = VenueForm(request.form)
  venue_data = Venue.query.get(venue_id)
  if venue_data:
    if form.validate():
      seeking_talent = False
      seeking_description = ''
      if 'seeking_talent' in request.form:
        seeking_talent = request.form['seeking_talent'] == 'y'
      if 'seeking_description' in request.form:
        seeking_description = request.form['seeking_description']
        setattr(venue_data, 'name', request.form['name'])
        setattr(venue_data, 'genres', request.form.getlist('genres'))
        setattr(venue_data, 'address', request.form['address'])
        setattr(venue_data, 'city', request.form['city'])
        setattr(venue_data, 'state', request.form['state'])
        setattr(venue_data, 'phone', request.form['phone'])
        setattr(venue_data, 'website', request.form['website_link'])
        setattr(venue_data, 'facebook_link', request.form['facebook_link'])
        setattr(venue_data, 'image_link', request.form['image_link'])
        setattr(venue_data, 'seeking_description', seeking_description)
        setattr(venue_data, 'seeking_talent', seeking_talent)

        # update the venue using try except to catch any errors
        try:
          # update the venue object in the database
          db.session.commit()
          # on successful db update, flash success
          flash('Venue ' + request.form['name'] + ' was successfully updated!')
        except:
          # rollback the session
          db.session.rollback()
        finally:
          # close the session
          db.session.close()
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
      print(form.errors)
  return render_template('errors/404.html'), 404

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  # TODO: insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  error = False
  try:
    seeking_venue = False
    seeking_description = ''
    if 'seeking_venue' in request.form:
      seeking_venue = request.form['seeking_venue'] == 'y'
    if 'seeking_description' in request.form:
      seeking_description = request.form['seeking_description']
    artist = Artist(
      name=request.form['name'],
      genres=request.form['genres'],
      city=request.form['city'],
      state= request.form['state'],
      phone=request.form['phone'],
      website=request.form['website_link'],
      image_link=request.form['image_link'],
      facebook_link=request.form['facebook_link'],
      seeking_venue=seeking_venue,
      seeking_description=seeking_description,
    )
    # insert the new venue object into the database
    db.session.add(artist)
    db.session.commit()
  except:
    error = True
    # rollback the session
    db.session.rollback()
  finally:
    db.session.close()
  if error:
    #on unsuccessful db insert, flash an error instead.
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Artist ' + request.form['name'] + ' was successfully listed!')

  return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: replace with real venues data.
  show_query = Show.query.options(db.joinedload(Show.Venue), db.joinedload(Show.Artist)).all()
  data = list(map(Show.detail, show_query))
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  # TODO: insert form data as a new Show record in the db, instead

  error = False

  # use try except to catch any errors
  try:
    # create a new show object
    show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time']
    )
    # insert the new show object into the database
    db.session.add(show)
    db.session.commit()
  except:
    error = True
    # rollback the session
    db.session.rollback()
  finally:
    # close the session
    db.session.close()
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
