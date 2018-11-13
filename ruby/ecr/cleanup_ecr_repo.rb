#!/usr/bin/env ruby
require 'aws-sdk'
require 'date'
require 'pp'

repo_name = ARGV[0]
if repo_name.nil?
  puts "Usage: #{$0} REPOSITORY_NAME"
  exit
end

DRY_RUN = ENV.fetch('DRY_RUN', true)
STALE_AFTER_DAYS = 30
STALE_BEFORE = DateTime.now() - STALE_AFTER_DAYS
ECR = Aws::ECR::Client.new(region: ENV.fetch('AWS_REGION', 'us-east-1'))

puts "Images considered stale if pushed before #{STALE_BEFORE}"

def get_ecr_repos(next_token = nil)
  params = {
    max_results: 50
  }
  params[:next_token] = next_token unless next_token.nil?
  ECR.describe_repositories(params)
end

def all_repos
  repositories = []
  next_token = nil
  while true
    resp = get_ecr_repos(next_token)
    break if resp.repositories.empty?
    resp.repositories.each {|repository| repositories << repository}
    next_token = resp.next_token
    break if next_token.nil?
  end
  return repositories
end

def get_ecr_images(repository_name, next_token = nil)
  params = {
    max_results: 100,
    repository_name: repository_name
  }
  params[:next_token] = next_token unless next_token.nil?
  ECR.describe_images(params)
end

def images_for_repo(repository_name)
  images = []
  next_token = nil
  while true
    resp = get_ecr_images(repository_name, next_token)
    break if resp.image_details.empty?
    resp.image_details.each {|image| images << image}
    next_token = resp.next_token
    break if next_token.nil?
  end
  return images
end

to_remove = {}
images_for_repo(repo_name).each do |image|
  if DateTime.parse("#{image.image_pushed_at}") < STALE_BEFORE
    next if image.image_tags.nil?
    next if image.image_tags.join('').include?('master')
    puts "#{image.image_tags.join('')}: #{image.image_pushed_at}"
    to_remove[image.registry_id] = [] if to_remove[image.registry_id].nil?
    to_remove[image.registry_id] << image.image_digest
  end
end

unless DRY_RUN == true
  puts "DRY_RUN is 'false' - proceeding with image removal"
  to_remove.keys.each do |registry_id|
    to_remove[registry_id].each_slice(10) do |batch|
      image_ids = []
      batch.each {|x| image_ids << { image_digest: x }}
      params = { "registry_id": registry_id, "repository_name": repo_name, "image_ids": image_ids}
      begin
        resp = ECR.batch_delete_image(params)
        puts resp.image_ids
        images_removed += resp.image_ids.length
      rescue
        puts resp.failures
      end
    end
  end
else
  puts "DRY_RUN" 
end
