import React from 'react';

import Count from '../components/count';
import ReleaseStats from '../components/releaseStats';
import TooltipMixin from '../mixins/tooltip';
import TimeSince from '../components/timeSince';
import Version from '../components/version';

export default React.createClass({
  propTypes: {
    orgId: React.PropTypes.string.isRequired,
    projectId: React.PropTypes.string.isRequired,
    releaseList: React.PropTypes.array.isRequired
  },

  mixins: [
    TooltipMixin({
      selector: '.tip'
    }),
  ],

  renderReleaseWeight(release) {
    let width = release.commitCount / release.projectCommitStats.maxCommits * 100;
    let commitCount = Math.round(
      (release.commitCount - release.projectCommitStats.avgCommits) * 100) / 100;
    let fullBar = {
      width: '100%',
      backgroundColor: '#d3d3d3',
      height: '4px',
      borderRadius: '3px',
    };
    let percentageBar = {
      width: width + '%',
      backgroundColor: commitCount > 5 ? '#e5685f' : '#c1bbc7',
      height: '4px',
      margin: '2px 0 6px'
    };
    if (width === 100) {
      percentageBar.borderRadius = '3px';
    } else {
      percentageBar.borderBottomLeftRadius = '3px';
      percentageBar.borderTopLeftRadius = '3px';
    }
    let title;
    if (commitCount === 0) {
      title = 'This release has an average number of commits for this project';
    } else if (commitCount > 0) {
      title = ('This release has ' + commitCount +
               ' more commits than average for this project');
    } else {
      title = ('This release has ' + Math.abs(commitCount) +
               ' fewer commits than average for this project');
    }
    return (
      <div className="tip" title={title} style={fullBar}>
        <div style={percentageBar}></div>
      </div>
    );
  },

  render() {
    let {orgId, projectId} = this.props;

    return (
      <ul className="list-group list-group-lg">
          {this.props.releaseList.map((release) => {
            return (
              <li className="list-group-item" key={release.version}>
                <div className="row row-center-vertically">
                  <div className="col-sm-4 col-xs-6">
                    <h2>
                      <Version orgId={orgId} projectId={projectId} version={release.version} />
                        &nbsp;
                        {this.renderReleaseWeight(release)}
                    </h2>
                    <p className="m-b-0 text-light" style={{marginTop: 6}}>
                      <span className="icon icon-clock"></span> <TimeSince date={release.dateCreated} />
                    </p>
                  </div>
                  <div className="col-sm-4 hidden-xs">
                    <ReleaseStats release={release}/>
                  </div>
                  <div className="col-sm-2 col-xs-3 text-big text-light">
                    <Count className="release-count" value={release.newGroups} />
                  </div>
                  <div className="col-sm-2 col-xs-3 text-light">
                    {release.lastEvent ?
                      <TimeSince date={release.lastEvent} />
                    :
                      <span>&mdash;</span>
                    }
                  </div>
                </div>
              </li>
            );
          })}
      </ul>
    );
  }
});
