'use strict';

var path = require('path');
var webpack = require('webpack');
var extract = require('extract-text-webpack-plugin');
var merge = require('webpack-merge');


var TARGET = process.env.npm_lifecycle_event;


const PATHS = {
    app: path.join(__dirname, 'frontend', 'index.js'),
    build: path.join(__dirname, 'med_social', 'static', 'build')
}

var config = {
    entry: PATHS.app,
    output: {
        path: PATHS.build,
        filename: 'bundle.js'
    },
    module: {
        loaders: [
            {
                test: /\.css$/,
                loader: extract.extract("style-loader", "css-loader")
            },
            {
                test: /\.jsx?$/,
                loader: 'babel',
                exclude: /(node_modules|bower_components)/,
                query: {
                    presets: ['es2015']
                }
            }
        ]
    },
    devtool: 'source-map',
    plugins: [
        new extract("styles.css")
        // new webpack.ProvidePlugin({
        //     $: "jquery",
        //     jQuery: "jquery",
        //     "window.jQuery": "jquery"
        // })
    ]
}


if (TARGET === 'build') {
    config = merge(config, {
        plugins: [
            new webpack.DefinePlugin({
                'process.env.NODE_ENV': JSON.stringify('production')
            }),
            new webpack.optimize.UglifyJsPlugin({
                'process.env.NODE_ENV': JSON.stringify('production')
            })
        ]
    })
}

module.exports = config;